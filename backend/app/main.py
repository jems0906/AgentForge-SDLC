from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import APP_ENV
from app.database import Base, engine, get_db
from app.models import AgentTask, CodeReview, QualityMetric, SandboxExecution, WorkflowExecution
from app.providers import get_provider
from app.sandbox.allowlist import COMMANDS
from app.sandbox.executor import execute
from app.schemas import ReviewDecision, SandboxRequest, TaskCreate, TaskRead
from app.orchestrator.workflow_templates import WORKFLOWS


if APP_ENV != "production":
    Base.metadata.create_all(bind=engine)
app = FastAPI(title="AgentForge SDLC", version="0.1.0", description="AI coding workflow orchestration for a bundled property-management sample repository.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in __import__("os").getenv("CORS_ORIGINS", "*").split(",")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "api"}


@app.get("/api/providers")
def list_providers():
    import os
    return [
        {"id": "mock", "name": "Mock provider", "configured": True, "default": True},
        {"id": "anthropic", "name": "Anthropic Claude", "configured": bool(os.getenv("ANTHROPIC_API_KEY")), "default": False},
        {"id": "openai", "name": "OpenAI", "configured": bool(os.getenv("OPENAI_API_KEY")), "default": False},
        {"id": "gemini", "name": "Google Gemini", "configured": bool(os.getenv("GEMINI_API_KEY")), "default": False},
    ]


@app.get("/api/workflows")
def list_workflows():
    return [{"id": key, **value} for key, value in WORKFLOWS.items()]


@app.get("/api/workflows/runs")
def list_workflow_runs(db: Session = Depends(get_db)):
    runs = db.scalars(select(WorkflowExecution).order_by(desc(WorkflowExecution.created_at)).limit(50)).all()
    return [{"id": run.id, "template_id": run.template_id, "status": run.status, "current_step": run.current_step, "steps": run.steps, "task_id": run.task_id, "created_at": run.created_at} for run in runs]


@app.post("/api/tasks", response_model=TaskRead, status_code=201)
@app.post("/api/agents/run", response_model=TaskRead, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    try:
        get_provider(payload.provider)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    workflow = WORKFLOWS[payload.task_type]
    run = WorkflowExecution(template_id=payload.task_type, steps=[{"name": step, "status": "pending"} for step in workflow["steps"]])
    db.add(run)
    db.flush()
    task = AgentTask(**payload.model_dump(), workflow_id=run.id)
    db.add(task)
    db.flush()
    run.task_id = task.id
    db.commit()
    db.refresh(task)
    return task


@app.post("/api/workflows/{template_id}/run", response_model=TaskRead, status_code=201)
def run_workflow(template_id: str, payload: TaskCreate, db: Session = Depends(get_db)):
    if template_id not in WORKFLOWS:
        raise HTTPException(status_code=404, detail="Workflow template not found")
    return create_task(payload.model_copy(update={"task_type": template_id}), db)


@app.get("/api/tasks", response_model=list[TaskRead])
def list_tasks(db: Session = Depends(get_db)):
    return db.scalars(select(AgentTask).order_by(desc(AgentTask.created_at)).limit(100)).all()


@app.get("/api/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(AgentTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/api/reviews")
def list_reviews(db: Session = Depends(get_db)):
    reviews = db.scalars(select(CodeReview).order_by(desc(CodeReview.updated_at)).limit(100)).all()
    return [{"id": review.id, "task_id": review.task_id, "status": review.status, "summary": review.summary, "diff": review.diff, "comments": review.comments, "created_at": review.created_at, "updated_at": review.updated_at} for review in reviews]


@app.post("/api/reviews/{review_id}/decision")
def decide_review(review_id: int, payload: ReviewDecision, db: Session = Depends(get_db)):
    review = db.get(CodeReview, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    allowed = {
        "approve": {"review"}, "request_changes": {"review"}, "reject": {"review", "changes_requested"},
        "merge": {"approved"}, "deploy": {"merged"}, "rollback": {"deployed"},
    }
    if review.status not in allowed[payload.decision]:
        raise HTTPException(status_code=409, detail=f"Cannot {payload.decision} a review in '{review.status}' state")
    task = db.get(AgentTask, review.task_id)
    if payload.decision == "approve" and task and task.outputs.get("tests", {}).get("status") != "passed":
        raise HTTPException(status_code=409, detail="Approval requires a passing sandbox test run")
    transitions = {"approve": "approved", "request_changes": "changes_requested", "reject": "rejected", "merge": "merged", "deploy": "deployed", "rollback": "rolled_back"}
    review.status = transitions[payload.decision]
    if payload.note:
        review.comments = [*review.comments, {"severity": "human", "comment": payload.note}]
    if task:
        task.status = review.status
        if payload.decision == "request_changes":
            task.outputs = {**task.outputs, "change_request": payload.note}
            task.description = f"{task.description}\n\nRequested changes: {payload.note}"[:8000]
            task.status = "queued"
        if payload.decision in {"deploy", "rollback"}:
            db.add(QualityMetric(metric="deployment_rollback" if payload.decision == "rollback" else "deployment", value=1))
    if task and task.workflow_id:
        workflow = db.get(WorkflowExecution, task.workflow_id)
        if workflow:
            workflow.status = review.status
            workflow.current_step = "complete" if payload.decision in {"merge", "deploy", "rollback", "reject"} else "approval"
    db.commit()
    return {"id": review.id, "status": review.status, "task_status": task.status if task else None}


@app.get("/api/sandbox/commands")
def sandbox_commands():
    return [{"command": command} for command in COMMANDS]


@app.post("/api/sandbox/execute")
def run_sandbox(payload: SandboxRequest, db: Session = Depends(get_db)):
    try:
        result = execute(payload.command)
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    record = SandboxExecution(command=payload.command, **result)
    db.add(record)
    db.add(QualityMetric(metric="sandbox_pass", value=1 if result["status"] == "passed" else 0))
    db.commit()
    db.refresh(record)
    return {"id": record.id, "command": record.command, "status": record.status, "exit_code": record.exit_code, "stdout": record.stdout, "stderr": record.stderr, "duration_seconds": record.duration_seconds, "created_at": record.created_at}


@app.get("/api/sandbox/runs")
def list_sandbox_runs(db: Session = Depends(get_db)):
    runs = db.scalars(select(SandboxExecution).order_by(desc(SandboxExecution.created_at)).limit(30)).all()
    return [{"id": run.id, "command": run.command, "status": run.status, "exit_code": run.exit_code, "stdout": run.stdout, "stderr": run.stderr, "duration_seconds": run.duration_seconds, "created_at": run.created_at} for run in runs]


@app.get("/api/dashboards/ci-quality")
def ci_quality(db: Session = Depends(get_db)):
    tasks = db.scalars(select(AgentTask)).all()
    runs = db.scalars(select(SandboxExecution)).all()
    passed = sum(run.status == "passed" for run in runs)
    failed = sum(run.status in {"failed", "timeout"} for run in runs)
    completed = sum(task.status in {"approved", "merged", "deployed"} for task in tasks)
    failed_tasks = sum(task.status == "failed" for task in tasks)
    durations = [(task.completed_at - task.started_at).total_seconds() for task in tasks if task.started_at and task.completed_at]
    recent_metrics = db.scalars(select(QualityMetric).order_by(desc(QualityMetric.recorded_at)).limit(30)).all()
    return {
        "test_pass_rate": round(passed / len(runs) * 100, 1) if runs else 100,
        "lint_failures": sum(run.status in {"failed", "timeout"} and "ruff" in run.command for run in runs),
        "agent_success_rate": round(completed / (completed + failed_tasks) * 100, 1) if completed + failed_tasks else 100,
        "average_task_seconds": round(sum(durations) / len(durations), 1) if durations else 0,
        "failed_runs": failed,
        "tasks_total": len(tasks),
        "runs": [{"date": run.created_at.isoformat(), "status": run.status, "command": run.command} for run in runs[-14:]],
        "alerts": ["Test pass rate below 90%" for _ in [0] if runs and passed / len(runs) < 0.9],
        "metrics_recorded": len(recent_metrics),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
