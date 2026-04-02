"""
Pipeline API endpoints.

  GET    /pipelines/                         list available pipelines
  GET    /pipelines/{id}                     get pipeline definition
  POST   /pipelines/{id}/run                 start execution → SSE stream
  POST   /pipelines/executions/{eid}/resume  supply user_input / file_id to resume paused execution
  GET    /pipelines/executions/{eid}         poll execution state
  GET    /pipelines/executions/              list user's executions
  DELETE /pipelines/executions/{eid}         cancel a running or paused execution
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.auth import TokenPayload, build_user_context, get_current_user
from app.repositories.pipeline_repository import PipelineRepository
from app.services.pipelines.executor import PipelineExecutor, create_execution

router = APIRouter(prefix="/pipelines", tags=["pipelines"])

CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]


# ── Schemas ───────────────────────────────────────────────────────────────────

class RunRequest(BaseModel):
    user_params: dict = {}
    session_id: str | None = None


class ResumeRequest(BaseModel):
    text: str | None = None       # for user_input steps
    file_id: str | None = None    # for file_input steps


# ── Pipeline catalogue ────────────────────────────────────────────────────────

@router.get("/")
async def list_pipelines(payload: CurrentUser):
    """Returns pipelines the user's groups can access."""
    repo = PipelineRepository()
    all_pipelines = await repo.list_for_tenant(payload.tenant)
    accessible = [
        p for p in all_pipelines
        if not p.allowed_groups or any(g in payload.groups for g in p.allowed_groups)
    ]
    return [
        {
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "description": p.description,
            "icon": p.icon,
            "category": p.category,
            "user_params": p.user_params,
            "allow_user_customization": p.allow_user_customization,
            "step_count": len(p.steps),
        }
        for p in accessible
    ]


@router.get("/{pipeline_id}")
async def get_pipeline(pipeline_id: str, payload: CurrentUser):
    repo = PipelineRepository()
    pipeline = await repo.get_by_id(pipeline_id, payload.tenant)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    _check_access(pipeline, payload.groups)
    return pipeline


# ── Run ───────────────────────────────────────────────────────────────────────

@router.post("/{pipeline_id}/run")
async def run_pipeline(pipeline_id: str, body: RunRequest, payload: CurrentUser):
    """
    Starts a pipeline execution and streams SSE events until completion or pause.

    The client should:
    1. Open this as an EventSource / fetch with stream reading.
    2. If it receives a `pipeline_paused` event, present the prompt to the user
       and call POST /pipelines/executions/{id}/resume.
    3. On `pipeline_complete` the execution is done.

    The X-Execution-Id response header carries the execution ID for polling / resume.
    """
    repo = PipelineRepository()
    pipeline = await repo.get_by_id(pipeline_id, payload.tenant)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    _check_access(pipeline, payload.groups)

    # Validate required user_params
    for param in pipeline.user_params:
        if param.required and param.key not in body.user_params:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing required parameter: {param.key!r}",
            )

    session_id = body.session_id or pipeline_id
    user_ctx = build_user_context(payload, session_id)
    execution = await create_execution(pipeline, user_ctx, body.user_params)
    executor = PipelineExecutor(pipeline, execution, user_ctx)

    return StreamingResponse(
        executor.run(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Execution-Id": execution.id,
        },
    )


# ── Resume ────────────────────────────────────────────────────────────────────

@router.post("/executions/{execution_id}/resume")
async def resume_pipeline(
    execution_id: str,
    body: ResumeRequest,
    payload: CurrentUser,
):
    """
    Supplies user input to a paused pipeline and resumes execution.
    Streams SSE events from the next step until the next pause or completion.
    """
    repo = PipelineRepository()
    execution = await repo.get_execution(execution_id)
    if not execution or execution.tenant != payload.tenant or execution.user_id != payload.sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

    if execution.status != "paused":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Execution is not paused (status={execution.status!r})",
        )

    pipeline = await repo.get_by_id(execution.pipeline_id, payload.tenant)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")

    user_ctx = build_user_context(payload, execution.pipeline_id)
    executor = PipelineExecutor(pipeline, execution, user_ctx)

    resume_input = {k: v for k, v in body.model_dump().items() if v is not None}

    return StreamingResponse(
        executor.resume(resume_input),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Execution-Id": execution_id,
        },
    )


# ── Execution state ───────────────────────────────────────────────────────────

@router.get("/executions/")
async def list_executions(payload: CurrentUser, pipeline_id: str | None = None):
    """Lists the user's pipeline executions, newest first."""
    from app.core.database import get_db
    db = get_db()
    query: dict = {"user_id": payload.sub, "tenant": payload.tenant}
    if pipeline_id:
        query["pipeline_id"] = pipeline_id
    cursor = db["pipeline_executions"].find(query).sort("created_at", -1).limit(50)
    return [
        {**doc, "_id": str(doc["_id"])}
        async for doc in cursor
    ]


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str, payload: CurrentUser):
    """Returns the current state of an execution (for polling)."""
    repo = PipelineRepository()
    execution = await repo.get_execution(execution_id)
    if not execution or execution.tenant != payload.tenant or execution.user_id != payload.sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return execution


@router.delete("/executions/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_execution(execution_id: str, payload: CurrentUser):
    """Cancels a running or paused execution (marks as failed)."""
    repo = PipelineRepository()
    execution = await repo.get_execution(execution_id)
    if not execution or execution.tenant != payload.tenant or execution.user_id != payload.sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

    if execution.status in ("completed", "failed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel an execution with status {execution.status!r}",
        )

    from datetime import datetime
    execution.status = "failed"
    execution.updated_at = datetime.utcnow()
    await repo.update_execution(execution)


# ── Helper ────────────────────────────────────────────────────────────────────

def _check_access(pipeline, groups: list[str]) -> None:
    if pipeline.allowed_groups and not any(g in groups for g in pipeline.allowed_groups):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
