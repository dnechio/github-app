from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.admin_auth import require_admin
from app.core.auth import TokenPayload
from app.models.pipeline import PipelineConfig, PipelineStep, PipelineParam
from app.repositories.pipeline_repository import PipelineRepository

router = APIRouter(prefix="/admin/pipelines", tags=["admin:pipelines"])

Tenant = Annotated[TokenPayload, Depends(require_admin)]


class PipelineCreateRequest(PipelineConfig):
    """Reuses PipelineConfig directly — id and tenant are overridden server-side."""
    id: str = ""
    tenant: str = ""


@router.get("/")
async def list_pipelines(payload: Tenant):
    repo = PipelineRepository()
    return await repo.list_for_tenant(payload.tenant, enabled_only=False)


@router.get("/{pipeline_id}")
async def get_pipeline(pipeline_id: str, payload: Tenant):
    repo = PipelineRepository()
    pipeline = await repo.get_by_id(pipeline_id, payload.tenant)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return pipeline


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_pipeline(body: PipelineCreateRequest, payload: Tenant):
    config = body.model_copy(update={"id": "", "tenant": payload.tenant})
    repo = PipelineRepository()
    new_id = await repo.upsert(config)
    return {"id": new_id}


@router.put("/{pipeline_id}")
async def update_pipeline(pipeline_id: str, body: PipelineCreateRequest, payload: Tenant):
    repo = PipelineRepository()
    existing = await repo.get_by_id(pipeline_id, payload.tenant)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    updated = body.model_copy(
        update={"id": pipeline_id, "tenant": payload.tenant, "updated_at": datetime.utcnow()}
    )
    await repo.upsert(updated)
    return {"id": pipeline_id}


@router.patch("/{pipeline_id}/toggle")
async def toggle_pipeline(pipeline_id: str, payload: Tenant):
    repo = PipelineRepository()
    pipeline = await repo.get_by_id(pipeline_id, payload.tenant)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    updated = pipeline.model_copy(
        update={"enabled": not pipeline.enabled, "updated_at": datetime.utcnow()}
    )
    await repo.upsert(updated)
    return {"id": pipeline_id, "enabled": updated.enabled}


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(pipeline_id: str, payload: Tenant):
    repo = PipelineRepository()
    deleted = await repo.delete(pipeline_id, payload.tenant)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
