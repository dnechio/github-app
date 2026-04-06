"""
File upload flow endpoints.

  POST   /files/upload             → validate + presigned PUT URL
  POST   /files/{id}/confirm       → mark queued + enqueue processor
  GET    /files/                   → list user files
  GET    /files/{id}               → get file status
  POST   /files/{id}/reprocess     → retry failed file
  DELETE /files/{id}               → soft delete
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import TokenPayload, build_user_context, get_current_user
from app.core.queue import enqueue_file_processing
from app.repositories.user_file_repository import UserFileRepository
from app.services.files.upload_service import (
    MAX_FILE_BYTES,
    ALLOWED_MIME_TYPES,
    build_s3_key,
    build_user_file,
    generate_presigned_put,
    resolve_file_type,
)

router = APIRouter(prefix="/files", tags=["files"])

CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]


# ── Request / response schemas ────────────────────────────────────────────────

class UploadRequest(BaseModel):
    filename: str
    mime_type: str
    file_size: int = Field(gt=0)
    session_id: str | None = None    # attach file to a specific chat session


class UploadResponse(BaseModel):
    file_id: str
    upload_url: str     # presigned PUT URL — client uploads directly to S3
    s3_key: str
    expires_in: int     # seconds until presigned URL expires


class ConfirmResponse(BaseModel):
    file_id: str
    status: str
    task_id: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse)
async def request_upload(body: UploadRequest, payload: CurrentUser):
    """
    Step 1 — Client calls this before uploading.

    Validates the file type and size, persists a UserFile record with
    status=uploading, then returns a presigned S3 PUT URL valid for 120 min.
    The client should PUT the file bytes directly to that URL.
    """
    # Validate mime type
    try:
        resolve_file_type(body.mime_type)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc))

    # Validate size
    if body.file_size > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_BYTES // (1024*1024)} MB",
        )

    user_ctx = build_user_context(payload, body.session_id or str(uuid.uuid4()))
    file_id = uuid.uuid4().hex
    s3_key = build_s3_key(payload.tenant, payload.sub, file_id, body.filename)

    user_file = build_user_file(
        file_id=file_id,
        s3_key=s3_key,
        filename=body.filename,
        mime_type=body.mime_type,
        file_size=body.file_size,
        user_ctx=user_ctx,
        session_id=body.session_id,
    )

    repo = UserFileRepository()
    db_id = await repo.create(user_file)

    upload_url = generate_presigned_put(s3_key, body.mime_type)

    return UploadResponse(
        file_id=db_id,
        upload_url=upload_url,
        s3_key=s3_key,
        expires_in=7200,
    )


@router.post("/{file_id}/confirm", response_model=ConfirmResponse)
async def confirm_upload(file_id: str, payload: CurrentUser):
    """
    Step 2 — Client calls this after the S3 PUT succeeds.

    Marks the file as queued and dispatches it to the file-processor worker.
    """
    repo = UserFileRepository()
    user_file = await repo.get_by_id(file_id, payload.sub, payload.tenant)

    if not user_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if user_file.status != "uploading":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"File is already in status {user_file.status!r}",
        )

    file_type = resolve_file_type(user_file.mime_type)

    await repo.update_status(file_id, "queued")

    task_id = await enqueue_file_processing(
        file_id=file_id,
        tenant_id=payload.tenant,
        user_id=payload.sub,
        file_type=file_type,
    )

    return ConfirmResponse(file_id=file_id, status="queued", task_id=task_id)


@router.get("/")
async def list_files(
    payload: CurrentUser,
    session_id: str | None = None,
):
    """Lists the current user's files, optionally filtered by session."""
    repo = UserFileRepository()
    files = await repo.list_for_user(
        user_id=payload.sub,
        tenant_id=payload.tenant,
        session_id=session_id,
    )
    return files


@router.get("/{file_id}")
async def get_file(file_id: str, payload: CurrentUser):
    """Returns the current status and metadata of a single file."""
    repo = UserFileRepository()
    user_file = await repo.get_by_id(file_id, payload.sub, payload.tenant)
    if not user_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return user_file


@router.post("/{file_id}/reprocess", response_model=ConfirmResponse)
async def reprocess_file(file_id: str, payload: CurrentUser):
    """
    Retries processing a file in status=failed.
    Resets the status to queued and re-enqueues the task.
    """
    repo = UserFileRepository()
    user_file = await repo.get_by_id(file_id, payload.sub, payload.tenant)

    if not user_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if user_file.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Only failed files can be reprocessed (current status: {user_file.status!r})",
        )

    if user_file.retry_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Maximum retry attempts reached",
        )

    file_type = resolve_file_type(user_file.mime_type)
    await repo.update_status(file_id, "queued", {"error_message": None})

    task_id = await enqueue_file_processing(
        file_id=file_id,
        tenant_id=payload.tenant,
        user_id=payload.sub,
        file_type=file_type,
    )

    return ConfirmResponse(file_id=file_id, status="queued", task_id=task_id)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: str, payload: CurrentUser):
    """Soft-deletes a file (status=deleted). Does not remove from S3 or Qdrant immediately."""
    repo = UserFileRepository()
    deleted = await repo.soft_delete(file_id, payload.sub, payload.tenant)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
