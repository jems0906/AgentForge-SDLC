import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import AgentTask, WorkflowExecution  # noqa: E402
from app.orchestrator.workflow_templates import WORKFLOWS  # noqa: E402


def main():
    Base.metadata.create_all(bind=engine)
    samples = json.loads((ROOT / "data_samples" / "agent_tasks.json").read_text(encoding="utf-8"))
    with SessionLocal() as db:
        existing = set(db.query(AgentTask.title).all())
        for sample in samples:
            if (sample["title"],) in existing:
                continue
            workflow_type = sample["task_type"]
            workflow = WorkflowExecution(
                template_id=workflow_type,
                steps=[{"name": step, "status": "pending"} for step in WORKFLOWS[workflow_type]["steps"]],
            )
            db.add(workflow)
            db.flush()
            task = AgentTask(**sample, workflow_id=workflow.id)
            db.add(task)
            db.flush()
            workflow.task_id = task.id
        db.commit()
    print(f"Seeded {len(samples)} sample task definitions (existing titles were skipped).")


if __name__ == "__main__":
    main()
