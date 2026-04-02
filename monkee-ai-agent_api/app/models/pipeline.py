from pydantic import BaseModel, Field
from typing import Literal, Any
from datetime import datetime


class PipelineStep(BaseModel):
    id: str
    type: Literal[
        "agent_call", "team_call", "file_input", "user_input",
        "tool_call", "conditional", "parallel", "transform"
    ]
    name: str
    config: dict[str, Any] = Field(default_factory=dict)
    next_step_id: str | None = None


class PipelineParam(BaseModel):
    key: str
    label: str
    type: Literal["text", "select", "boolean"]
    options: list[str] = Field(default_factory=list)
    default: Any = None
    required: bool = False


class PipelineConfig(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    tenant: str
    enabled: bool = True
    icon: str = "pipeline"
    category: str = "general"

    steps: list[PipelineStep] = Field(default_factory=list)
    user_params: list[PipelineParam] = Field(default_factory=list)
    allow_user_customization: bool = False

    allowed_groups: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PipelineExecution(BaseModel):
    id: str
    pipeline_id: str
    user_id: str
    tenant: str
    status: Literal["running", "paused", "completed", "failed"] = "running"
    current_step: int = 0
    steps_results: list[dict[str, Any]] = Field(default_factory=list)
    user_params: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
