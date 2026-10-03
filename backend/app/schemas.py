from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(default="", max_length=8000)
    task_type: str = Field(default="feature", pattern="^(feature|bugfix|refactor|test|integration)$")
    provider: str = Field(default="mock", pattern="^(mock|anthropic|openai|gemini)$")


class TaskRead(TaskCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    workflow_id: int | None = None
    outputs: dict[str, Any] = Field(default_factory=dict)


class WorkflowRun(BaseModel):
    task_id: int


class ReviewDecision(BaseModel):
    decision: str = Field(pattern="^(approve|request_changes|reject|merge|deploy|rollback)$")
    note: str = Field(default="", max_length=2000)


class SandboxRequest(BaseModel):
    command: str = Field(min_length=1, max_length=120)
