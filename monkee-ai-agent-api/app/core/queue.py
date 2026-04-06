"""
Thin async wrapper around Redis to enqueue tasks for the file-processor worker.
Uses the same Redis instance as Celery so tasks land in the default Celery queue.
"""
import json
import uuid

import redis.asyncio as aioredis

from app.core.config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def _enqueue(task_name: str, kwargs: dict) -> str:
    """Pushes a Celery-compatible task message onto the default queue."""
    task_id = uuid.uuid4().hex
    message = {
        "id": task_id,
        "task": task_name,
        "kwargs": kwargs,
        "args": [],
    }
    r = await get_redis()
    await r.lpush("celery", json.dumps(message))
    return task_id


async def enqueue_file_processing(
    *,
    file_id: str,
    tenant_id: str,
    user_id: str,
    file_type: str,
) -> str:
    return await _enqueue(
        "process_file",
        {"file_id": file_id, "tenant_id": tenant_id, "user_id": user_id, "file_type": file_type},
    )


async def enqueue_kb_indexing(
    *,
    file_id: str,
    s3_key: str,
    kb_id: str,
    vector_collection: str,
    tenant_id: str,
    chunking_strategy: str,
    chunk_size: int,
    chunk_overlap: int,
) -> str:
    return await _enqueue(
        "index_kb_document",
        {
            "file_id": file_id,
            "s3_key": s3_key,
            "kb_id": kb_id,
            "vector_collection": vector_collection,
            "tenant_id": tenant_id,
            "chunking_strategy": chunking_strategy,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        },
    )
