from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.agent import AgentConfig
from app.core.database import get_db


class AgentRepository:
    COLLECTION = "agents"

    def __init__(self, db: AsyncIOMotorDatabase | None = None):
        self._db = db or get_db()

    @property
    def col(self):
        return self._db[self.COLLECTION]

    async def get_by_id(self, agent_id: str, tenant_id: str) -> AgentConfig | None:
        doc = await self.col.find_one({"_id": ObjectId(agent_id), "tenant": tenant_id})
        return AgentConfig(**{**doc, "id": str(doc["_id"])}) if doc else None

    async def get_by_slug(self, slug: str, tenant_id: str) -> AgentConfig | None:
        doc = await self.col.find_one({"slug": slug, "tenant": tenant_id, "enabled": True})
        return AgentConfig(**{**doc, "id": str(doc["_id"])}) if doc else None

    async def list_for_tenant(self, tenant_id: str, enabled_only: bool = True) -> list[AgentConfig]:
        query: dict = {"tenant": tenant_id}
        if enabled_only:
            query["enabled"] = True
        cursor = self.col.find(query).sort("name", 1)
        return [AgentConfig(**{**doc, "id": str(doc["_id"])}) async for doc in cursor]

    async def list_for_group(self, tenant_id: str, groups: list[str]) -> list[AgentConfig]:
        cursor = self.col.find({
            "tenant": tenant_id,
            "enabled": True,
            "$or": [
                {"allowed_groups": {"$size": 0}},
                {"allowed_groups": {"$in": groups}},
            ],
        }).sort("name", 1)
        return [AgentConfig(**{**doc, "id": str(doc["_id"])}) async for doc in cursor]

    async def upsert(self, config: AgentConfig) -> str:
        data = config.model_dump(exclude={"id"})
        if config.id:
            await self.col.replace_one({"_id": ObjectId(config.id)}, data, upsert=True)
            return config.id
        result = await self.col.insert_one(data)
        return str(result.inserted_id)

    async def delete(self, agent_id: str, tenant_id: str) -> bool:
        result = await self.col.delete_one({"_id": ObjectId(agent_id), "tenant": tenant_id})
        return result.deleted_count > 0
