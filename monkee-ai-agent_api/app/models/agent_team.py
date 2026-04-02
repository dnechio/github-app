from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class AgentTeam(BaseModel):
    id: str = ""
    name: str
    slug: str
    description: str
    tenant: str
    enabled: bool = True

    mode: Literal["collaborate", "route", "coordinate"] = "route"
    leader_agent_id: str | None = None     # Required for mode="route"
    member_agent_ids: list[str] = Field(default_factory=list)
    instructions: str = ""

    # Routing metadata (used by RouterAgent)
    routing_description: str = ""
    routing_tags: list[str] = Field(default_factory=list)

    allowed_groups: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
