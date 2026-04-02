from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.knowledge_base import KnowledgeBase
from app.core.database import get_db


class KnowledgeBaseRepository:
    COLLECTION = "knowledge_bases"

    def __init__(self, db: AsyncIOMotorDatabase | None = None):
        self._db = db or get_db()

    @property
    def col(self):
        return self._db[self.COLLECTION]

    async def get_by_id(self, kb_id: str, tenant_id: str) -> KnowledgeBase | None:
        doc = await self.col.find_one({"_id": ObjectId(kb_id), "tenant": tenant_id})
        return KnowledgeBase(**{**doc, "id": str(doc["_id"])}) if doc else None

    async def get_by_ids(self, kb_ids: list[str], tenant_id: str) -> list[KnowledgeBase]:
        object_ids = [ObjectId(i) for i in kb_ids if i]
        cursor = self.col.find({"_id": {"$in": object_ids}, "tenant": tenant_id})
        return [KnowledgeBase(**{**doc, "id": str(doc["_id"])}) async for doc in cursor]

    async def list_for_tenant(self, tenant_id: str) -> list[KnowledgeBase]:
        cursor = self.col.find({"tenant": tenant_id}).sort("name", 1)
        return [KnowledgeBase(**{**doc, "id": str(doc["_id"])}) async for doc in cursor]

    async def upsert(self, kb: KnowledgeBase) -> str:
        data = kb.model_dump(exclude={"id"})
        if kb.id:
            await self.col.replace_one({"_id": ObjectId(kb.id)}, data, upsert=True)
            return kb.id
        result = await self.col.insert_one(data)
        return str(result.inserted_id)

    async def update_stats(self, kb_id: str, total_docs: int, total_chunks: int) -> None:
        from datetime import datetime
        await self.col.update_one(
            {"_id": ObjectId(kb_id)},
            {"$set": {
                "stats.total_documents": total_docs,
                "stats.total_chunks": total_chunks,
                "stats.last_indexed_at": datetime.utcnow(),
            }},
        )

    async def delete(self, kb_id: str, tenant_id: str) -> bool:
        result = await self.col.delete_one({"_id": ObjectId(kb_id), "tenant": tenant_id})
        return result.deleted_count > 0
