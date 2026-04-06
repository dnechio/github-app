from pydantic import BaseModel, Field
from datetime import datetime


class UserProfile(BaseModel):
    id: str = ""
    tenant: str
    name: str
    email: str
    api_key_hash: str         # SHA-256 of the raw API key
    groups: list[str] = Field(default_factory=list)
    enabled: bool = True

    # Usage quota overrides (None = use agent defaults)
    day_limit_override: int | None = None
    week_limit_override: int | None = None
    month_limit_override: int | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserGroup(BaseModel):
    id: str = ""
    tenant: str
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
