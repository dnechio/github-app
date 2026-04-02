from pydantic import BaseModel, Field
from datetime import datetime


class ToolConfig(BaseModel):
    id: str = ""
    name: str
    description: str
    tenant: str
    class_name: str           # Python class registered in the system
    icon: str = "tool"
    category: str = "general"

    params: dict = Field(default_factory=dict)   # api_key, endpoint, max_results, etc.
    enabled: bool = True
    allowed_agents: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
