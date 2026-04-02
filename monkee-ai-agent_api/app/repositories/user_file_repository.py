from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user_file import UserFile, FileStatus
from app.core.database import get_db


class UserFileRepository:
    COLLECTION = "user_files"

    def __init__(self, db: AsyncIOMotorDatabase | None = None):
        self._db = db or get_db()

    @property
    def col(self):
        return self._db[self.COLLECTION]

    async def create(self, user_file: UserFile) -> str:
        data = user_file.model_dump(exclude={"id"})
        result = await self.col.insert_one(data)
        return str(result.inserted_id)

    async def get_by_id(self, file_id: str, user_id: str, tenant_id: str) -> UserFile | None:
        doc = await self.col.find_one({
            "_id": ObjectId(file_id),
            "user_id": user_id,
            "tenant_id": tenant_id,
        })
        return UserFile(**{**doc, "id": str(doc["_id"])}) if doc else None

    async def get_by_id_admin(self, file_id: str, tenant_id: str) -> UserFile | None:
        """Admin access — not scoped to user_id."""
        doc = await self.col.find_one({"_id": ObjectId(file_id), "tenant_id": tenant_id})
        return UserFile(**{**doc, "id": str(doc["_id"])}) if doc else None

    async def list_for_user(
        self,
        user_id: str,
        tenant_id: str,
        session_id: str | None = None,
        exclude_deleted: bool = True,
    ) -> list[UserFile]:
        query: dict = {"user_id": user_id, "tenant_id": tenant_id}
        if session_id:
            query["session_id"] = session_id
        if exclude_deleted:
            query["status"] = {"$ne": "deleted"}
        cursor = self.col.find(query).sort("created_at", -1)
        return [UserFile(**{**doc, "id": str(doc["_id"])}) async for doc in cursor]

    async def update_status(
        self,
        file_id: str,
        status: FileStatus,
        extra: dict | None = None,
    ) -> None:
        update: dict = {"status": status}
        if status == "ready":
            update["processed_at"] = datetime.utcnow()
        if extra:
            update.update(extra)
        await self.col.update_one(
            {"_id": ObjectId(file_id)},
            {"$set": update},
        )

    async def increment_retry(self, file_id: str, error_message: str) -> None:
        await self.col.update_one(
            {"_id": ObjectId(file_id)},
            {
                "$inc": {"retry_count": 1},
                "$set": {"error_message": error_message, "status": "failed"},
            },
        )

    async def soft_delete(self, file_id: str, user_id: str, tenant_id: str) -> bool:
        result = await self.col.update_one(
            {"_id": ObjectId(file_id), "user_id": user_id, "tenant_id": tenant_id},
            {"$set": {"status": "deleted"}},
        )
        return result.modified_count > 0
