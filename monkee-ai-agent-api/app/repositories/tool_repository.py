from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.tool import ToolConfig
from app.core.database import get_db


class ToolRepository:
    COLLECTION = "tools"

    def __init__(self, db: AsyncIOMotorDatabase | None = None):
        self._db = db or get_db()

    @property
    def col(self):
        return self._db[self.COLLECTION]

    async def get_by_id(self, tool_id: str, tenant_id: str) -> ToolConfig | None:
        doc = await self.col.find_one({"_id": ObjectId(tool_id), "tenant": tenant_id})
        return ToolConfig(**{**doc, "id": str(doc["_id"])}) if doc else None

    async def list_for_tenant(self, tenant_id: str) -> list[ToolConfig]:
        cursor = self.col.find({"tenant": tenant_id}).sort("name", 1)
        return [ToolConfig(**{**doc, "id": str(doc["_id"])}) async for doc in cursor]

    async def upsert(self, config: ToolConfig) -> str:
        data = config.model_dump(exclude={"id"})
        if config.id:
            await self.col.replace_one({"_id": ObjectId(config.id)}, data, upsert=True)
            return config.id
        result = await self.col.insert_one(data)
        return str(result.inserted_id)

    async def delete(self, tool_id: str, tenant_id: str) -> bool:
        result = await self.col.delete_one({"_id": ObjectId(tool_id), "tenant": tenant_id})
        return result.deleted_count > 0
