from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


FileStatus = Literal[
    "uploading", "queued", "processing", "indexing", "ready", "failed", "deleted"
]


class UserFile(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    session_id: str | None = None

    # Metadata
    title: str
    extension: str
    mime_type: str
    bytes: int

    # Location
    s3_key: str
    vector_namespace: str

    # State
    status: FileStatus = "uploading"

    # Processing result
    extracted_text_key: str | None = None
    chunks_count: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None

    # Retry
    retry_count: int = 0
    error_message: str | None = None
