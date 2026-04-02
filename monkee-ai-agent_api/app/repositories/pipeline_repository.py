from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.pipeline import PipelineConfig, PipelineExecution
from app.core.database import get_db


class PipelineRepository:
    COLLECTION = "pipelines"
    EXEC_COLLECTION = "pipeline_executions"

    def __init__(self, db: AsyncIOMotorDatabase | None = None):
        self._db = db or get_db()

    @property
    def col(self):
        return self._db[self.COLLECTION]

    @property
    def exec_col(self):
        return self._db[self.EXEC_COLLECTION]

    async def get_by_id(self, pipeline_id: str, tenant_id: str) -> PipelineConfig | None:
        doc = await self.col.find_one({"_id": ObjectId(pipeline_id), "tenant": tenant_id})
        return PipelineConfig(**{**doc, "id": str(doc["_id"])}) if doc else None

    async def list_for_tenant(self, tenant_id: str, enabled_only: bool = True) -> list[PipelineConfig]:
        query: dict = {"tenant": tenant_id}
        if enabled_only:
            query["enabled"] = True
        cursor = self.col.find(query).sort("name", 1)
        return [PipelineConfig(**{**doc, "id": str(doc["_id"])}) async for doc in cursor]

    async def upsert(self, config: PipelineConfig) -> str:
        data = config.model_dump(exclude={"id"})
        if config.id:
            await self.col.replace_one({"_id": ObjectId(config.id)}, data, upsert=True)
            return config.id
        result = await self.col.insert_one(data)
        return str(result.inserted_id)

    async def delete(self, pipeline_id: str, tenant_id: str) -> bool:
        result = await self.col.delete_one({"_id": ObjectId(pipeline_id), "tenant": tenant_id})
        return result.deleted_count > 0

    # --- Executions ---

    async def create_execution(self, execution: PipelineExecution) -> str:
        data = execution.model_dump(exclude={"id"})
        result = await self.exec_col.insert_one(data)
        return str(result.inserted_id)

    async def get_execution(self, exec_id: str) -> PipelineExecution | None:
        doc = await self.exec_col.find_one({"_id": ObjectId(exec_id)})
        return PipelineExecution(**{**doc, "id": str(doc["_id"])}) if doc else None

    async def update_execution(self, execution: PipelineExecution) -> None:
        data = execution.model_dump(exclude={"id"})
        await self.exec_col.replace_one({"_id": ObjectId(execution.id)}, data)
