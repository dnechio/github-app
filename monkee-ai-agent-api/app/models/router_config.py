from pydantic import BaseModel, Field
from typing import Literal


class RoutingRule(BaseModel):
    pattern: str                         # regex or keywords
    target_type: Literal["agent", "pipeline", "team"]
    target_id: str
    priority: int = 0


class RouterConfig(BaseModel):
    id: str = ""
    tenant: str
    mode: Literal["llm", "rules", "hybrid"] = "llm"
    model: str = "gemini-2.0-flash"
    provider: str = "google"

    agent_ids: list[str] = Field(default_factory=list)
    pipeline_ids: list[str] = Field(default_factory=list)
    team_ids: list[str] = Field(default_factory=list)

    fallback_agent_id: str | None = None
    routing_rules: list[RoutingRule] = Field(default_factory=list)
