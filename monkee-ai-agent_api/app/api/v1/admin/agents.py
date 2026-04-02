from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.admin_auth import require_admin
from app.core.auth import TokenPayload
from app.models.agent import AgentConfig
from app.repositories.agent_repository import AgentRepository

router = APIRouter(prefix="/admin/agents", tags=["admin:agents"])

Tenant = Annotated[TokenPayload, Depends(require_admin)]


class AgentCreateRequest(BaseModel):
    name: str
    slug: str
    description: str
    model: str = "claude-sonnet-4-6"
    provider: str = "anthropic"
    instructions: str
    temperature: float = 0.7
    max_tokens: int = 4096
    reasoning_effort: str | None = None
    tools: list[str] = []
    knowledge_bases: list[str] = []
    can_use_user_files: bool = False
    can_use_memory: bool = True
    show_citations: bool = True
    routing_tags: list[str] = []
    routing_description: str = ""
    day_limit: int = 100
    week_limit: int = 500
    month_limit: int = 2000
    allowed_groups: list[str] = []
    enabled: bool = True


class AgentUpdateRequest(AgentCreateRequest):
    pass


@router.get("/")
async def list_agents(payload: Tenant):
    repo = AgentRepository()
    agents = await repo.list_for_tenant(payload.tenant, enabled_only=False)
    return agents


@router.get("/{agent_id}")
async def get_agent(agent_id: str, payload: Tenant):
    repo = AgentRepository()
    agent = await repo.get_by_id(agent_id, payload.tenant)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_agent(body: AgentCreateRequest, payload: Tenant):
    config = AgentConfig(
        id="",
        tenant=payload.tenant,
        **body.model_dump(),
    )
    repo = AgentRepository()
    new_id = await repo.upsert(config)
    return {"id": new_id}


@router.put("/{agent_id}")
async def update_agent(agent_id: str, body: AgentUpdateRequest, payload: Tenant):
    repo = AgentRepository()
    existing = await repo.get_by_id(agent_id, payload.tenant)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    updated = existing.model_copy(
        update={**body.model_dump(), "updated_at": datetime.utcnow()}
    )
    await repo.upsert(updated)
    return {"id": agent_id}


@router.patch("/{agent_id}/toggle")
async def toggle_agent(agent_id: str, payload: Tenant):
    repo = AgentRepository()
    agent = await repo.get_by_id(agent_id, payload.tenant)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    updated = agent.model_copy(update={"enabled": not agent.enabled, "updated_at": datetime.utcnow()})
    await repo.upsert(updated)
    return {"id": agent_id, "enabled": updated.enabled}


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str, payload: Tenant):
    repo = AgentRepository()
    deleted = await repo.delete(agent_id, payload.tenant)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
