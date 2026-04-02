from dataclasses import dataclass, field


@dataclass
class UserContext:
    user_id: str
    tenant_id: str
    session_id: str
    groups: list[str] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)

    @property
    def vector_namespace(self) -> str:
        return f"user_{self.tenant_id}_{self.user_id}"
