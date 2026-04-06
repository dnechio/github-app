"""
Synchronous MongoDB client for the Celery worker.
Motor (async) is not needed here — Celery tasks run in a sync context.
"""
from datetime import datetime
from functools import lru_cache

from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection

from app.core.config import settings


@lru_cache(maxsize=1)
def _client() -> MongoClient:
    return MongoClient(settings.MONGODB_URI)


def get_db():
    return _client()[settings.MONGODB_DB]


def get_files_col() -> Collection:
    return get_db()["user_files"]


def update_file_status(
    file_id: str,
    status: str,
    extra: dict | None = None,
) -> None:
    update: dict = {"status": status}
    if status == "ready":
        update["processed_at"] = datetime.utcnow()
    if extra:
        update.update(extra)
    get_files_col().update_one(
        {"_id": ObjectId(file_id)},
        {"$set": update},
    )


def increment_file_retry(file_id: str, error_message: str) -> None:
    get_files_col().update_one(
        {"_id": ObjectId(file_id)},
        {
            "$inc": {"retry_count": 1},
            "$set": {"error_message": error_message, "status": "failed"},
        },
    )


def get_file_s3_key(file_id: str) -> str | None:
    doc = get_files_col().find_one({"_id": ObjectId(file_id)}, {"s3_key": 1})
    return doc["s3_key"] if doc else None
