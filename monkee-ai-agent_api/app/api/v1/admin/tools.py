from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.admin_auth import require_admin
from app.core.auth import TokenPayload
from app.models.tool import ToolConfig
from app.repositories.tool_repository import ToolRepository

router = APIRouter(prefix="/admin/tools", tags=["admin:tools"])

Tenant = Annotated[TokenPayload, Depends(require_admin)]


class ToolCreateRequest(BaseModel):
    name: str
    description: str
    class_name: str
    icon: str = "tool"
    category: str = "general"
    params: dict = {}
    enabled: bool = True
    allowed_agents: list[str] = []


@router.get("/")
async def list_tools(payload: Tenant):
    repo = ToolRepository()
    return await repo.list_for_tenant(payload.tenant)


@router.get("/{tool_id}")
async def get_tool(tool_id: str, payload: Tenant):
    repo = ToolRepository()
    tool = await repo.get_by_id(tool_id, payload.tenant)
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    return tool


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_tool(body: ToolCreateRequest, payload: Tenant):
    config = ToolConfig(id="", tenant=payload.tenant, **body.model_dump())
    repo = ToolRepository()
    new_id = await repo.upsert(config)
    return {"id": new_id}


@router.put("/{tool_id}")
async def update_tool(tool_id: str, body: ToolCreateRequest, payload: Tenant):
    repo = ToolRepository()
    existing = await repo.get_by_id(tool_id, payload.tenant)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    updated = existing.model_copy(
        update={**body.model_dump(), "updated_at": datetime.utcnow()}
    )
    await repo.upsert(updated)
    return {"id": tool_id}


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(tool_id: str, payload: Tenant):
    repo = ToolRepository()
    deleted = await repo.delete(tool_id, payload.tenant)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
