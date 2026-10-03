import logging
import os
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.database import SessionLocal
from app.models import AgentTask, CodeReview, QualityMetric, SandboxExecution, WorkflowExecution
from app.orchestrator.workflow_templates import WORKFLOWS
from app.providers import get_provider
from app.sandbox.executor import execute


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("agentforge.worker")


def process_one() -> bool:
    try:
        with SessionLocal() as db:
            task = db.scalars(select(AgentTask).where(AgentTask.status == "queued").order_by(AgentTask.created_at).with_for_update(skip_locked=True)).first()
            if task is None:
                return False
            task.status = "running"
            task.started_at = datetime.now(timezone.utc)
            workflow = db.get(WorkflowExecution, task.workflow_id) if task.workflow_id else None
            if workflow:
                workflow.status = "running"
            db.commit()
            task_id = task.id
    except OperationalError:
        logger.info("Database schema is not ready; worker will retry")
        return False

    with SessionLocal() as db:
        task = db.get(AgentTask, task_id)
        workflow = db.get(WorkflowExecution, task.workflow_id) if task and task.workflow_id else None
        try:
            provider = get_provider(task.provider)
            task_data = {"title": task.title, "description": task.description, "task_type": task.task_type}
            plan = provider.generate_plan(task_data)
            proposal = provider.generate_code(task_data, plan)
            test_result = execute("pytest")
            comments = provider.review_code(proposal["diff"])
            task.outputs = {"plan": plan, "proposal": proposal, "tests": test_result}
            task.status = "in_review"
            task.completed_at = datetime.now(timezone.utc)
            review = CodeReview(task_id=task.id, status="review", summary=proposal["summary"], diff=proposal["diff"], comments=comments)
            db.add(review)
            db.add(SandboxExecution(command="pytest", **test_result))
            db.add(QualityMetric(metric="sandbox_pass", value=1 if test_result["status"] == "passed" else 0))
            if workflow:
                workflow.status = "in_review"
                workflow.current_step = "approval"
                workflow.steps = [{"name": name, "status": "completed" if name != "approval" else "waiting"} for name in WORKFLOWS[task.task_type]["steps"]]
            db.commit()
            logger.info("Task %s prepared for review; validation %s", task.id, test_result["status"])
        except Exception as error:
            logger.exception("Task %s failed", task.id)
            task.status = "failed"
            task.outputs = {**(task.outputs or {}), "error": str(error)}
            task.completed_at = datetime.now(timezone.utc)
            if workflow:
                workflow.status = "failed"
            db.commit()
    return True


def main():
    logger.info("AgentForge worker polling for tasks")
    while True:
        if not process_one():
            time.sleep(float(os.getenv("WORKER_POLL_SECONDS", "2")))


if __name__ == "__main__":
    main()
