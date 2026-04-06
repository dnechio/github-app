"""
File upload flow:

  1. POST /files/upload
       → validate mime/size/quota
       → create UserFile (status=uploading) in MongoDB
       → generate S3 presigned PUT URL (120 min)
       → return { file_id, upload_url, s3_key }

  2. Client PUT → S3 directly (no server in the middle)

  3. POST /files/{file_id}/confirm
       → mark status=queued
       → enqueue process_file task in Redis/Celery
       → return { file_id, status }
"""
import uuid
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from loguru import logger

from app.core.config import settings
from app.models.user_file import UserFile
from app.services.agents.context import UserContext


# ── Allowed types ────────────────────────────────────────────────────────────

ALLOWED_MIME_TYPES: dict[str, str] = {
    # Audio
    "audio/mpeg": "audio",
    "audio/wav": "audio",
    "audio/x-wav": "audio",
    "audio/mp4": "audio",
    "audio/m4a": "audio",
    "audio/ogg": "audio",
    "audio/flac": "audio",
    "audio/aac": "audio",
    # Video
    "video/mp4": "video",
    "video/quicktime": "video",
    "video/x-matroska": "video",
    "video/x-msvideo": "video",
    # PDF
    "application/pdf": "pdf",
    # Documents
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
    "application/msword": "document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "document",
    "text/plain": "document",
    "text/markdown": "document",
    "text/html": "document",
    # Images
    "image/png": "image",
    "image/jpeg": "image",
    "image/gif": "image",
    "image/webp": "image",
    "image/heic": "image",
    # JSON
    "application/json": "json",
}

MAX_FILE_BYTES = 500 * 1024 * 1024  # 500 MB
PRESIGNED_URL_EXPIRY = 7200         # 120 minutes


def _s3_client():
    kwargs = dict(
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    if settings.AWS_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.AWS_ENDPOINT_URL
    return boto3.client("s3", **kwargs)


def resolve_file_type(mime_type: str) -> str:
    file_type = ALLOWED_MIME_TYPES.get(mime_type)
    if not file_type:
        raise ValueError(f"Unsupported file type: {mime_type!r}")
    return file_type


def generate_presigned_put(s3_key: str, mime_type: str) -> str:
    s3 = _s3_client()
    try:
        url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.AWS_S3_BUCKET,
                "Key": s3_key,
                "ContentType": mime_type,
            },
            ExpiresIn=PRESIGNED_URL_EXPIRY,
        )
    except ClientError as exc:
        logger.error(f"Failed to generate presigned URL: {exc}")
        raise RuntimeError("Could not generate upload URL") from exc
    return url


def build_s3_key(tenant_id: str, user_id: str, file_id: str, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"users/{tenant_id}/{user_id}/{file_id}.{ext}"


def build_user_file(
    *,
    file_id: str,
    s3_key: str,
    filename: str,
    mime_type: str,
    file_size: int,
    user_ctx: UserContext,
    session_id: str | None,
) -> UserFile:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return UserFile(
        id="",
        tenant_id=user_ctx.tenant_id,
        user_id=user_ctx.user_id,
        session_id=session_id,
        title=filename,
        extension=ext,
        mime_type=mime_type,
        bytes=file_size,
        s3_key=s3_key,
        vector_namespace=user_ctx.vector_namespace,
        status="uploading",
        created_at=datetime.utcnow(),
    )
