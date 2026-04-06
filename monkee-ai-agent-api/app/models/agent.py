from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class AgentConfig(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    tenant: str
    enabled: bool = True

    # Model
    model: str = "claude-sonnet-4-6"
    provider: Literal["anthropic", "openai", "google", "groq"] = "anthropic"
    instructions: str
    temperature: float = 0.7
    max_tokens: int = 4096
    reasoning_effort: str | None = None

    # Capabilities
    tools: list[str] = Field(default_factory=list)
    knowledge_bases: list[str] = Field(default_factory=list)
    can_use_user_files: bool = False
    can_use_memory: bool = True
    show_citations: bool = True

    # Routing
    routing_tags: list[str] = Field(default_factory=list)
    routing_description: str = ""

    # Limits
    day_limit: int = 100
    week_limit: int = 500
    month_limit: int = 2000

    # Permissions
    allowed_groups: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
