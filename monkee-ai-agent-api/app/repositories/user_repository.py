import hashlib
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import UserProfile, UserGroup
from app.core.database import get_db


class UserRepository:
    USERS_COLLECTION = "users"
    GROUPS_COLLECTION = "user_groups"

    def __init__(self, db: AsyncIOMotorDatabase | None = None):
        self._db = db or get_db()

    @property
    def users(self):
        return self._db[self.USERS_COLLECTION]

    @property
    def groups(self):
        return self._db[self.GROUPS_COLLECTION]

    # --- Users ---

    async def get_by_id(self, user_id: str, tenant_id: str) -> UserProfile | None:
        doc = await self.users.find_one({"_id": ObjectId(user_id), "tenant": tenant_id})
        return UserProfile(**{**doc, "id": str(doc["_id"])}) if doc else None

    async def list_for_tenant(self, tenant_id: str) -> list[UserProfile]:
        cursor = self.users.find({"tenant": tenant_id}).sort("name", 1)
        return [UserProfile(**{**doc, "id": str(doc["_id"])}) async for doc in cursor]

    async def upsert(self, profile: UserProfile) -> str:
        data = profile.model_dump(exclude={"id"})
        if profile.id:
            await self.users.replace_one({"_id": ObjectId(profile.id)}, data, upsert=True)
            return profile.id
        result = await self.users.insert_one(data)
        return str(result.inserted_id)

    async def delete(self, user_id: str, tenant_id: str) -> bool:
        result = await self.users.delete_one({"_id": ObjectId(user_id), "tenant": tenant_id})
        return result.deleted_count > 0

    async def rotate_api_key(self, user_id: str, tenant_id: str, new_raw_key: str) -> bool:
        new_hash = hashlib.sha256(new_raw_key.encode()).hexdigest()
        result = await self.users.update_one(
            {"_id": ObjectId(user_id), "tenant": tenant_id},
            {"$set": {"api_key_hash": new_hash}},
        )
        return result.modified_count > 0

    # --- Groups ---

    async def list_groups(self, tenant_id: str) -> list[UserGroup]:
        cursor = self.groups.find({"tenant": tenant_id}).sort("name", 1)
        return [UserGroup(**{**doc, "id": str(doc["_id"])}) async for doc in cursor]

    async def upsert_group(self, group: UserGroup) -> str:
        data = group.model_dump(exclude={"id"})
        if group.id:
            await self.groups.replace_one({"_id": ObjectId(group.id)}, data, upsert=True)
            return group.id
        result = await self.groups.insert_one(data)
        return str(result.inserted_id)

    async def delete_group(self, group_id: str, tenant_id: str) -> bool:
        result = await self.groups.delete_one({"_id": ObjectId(group_id), "tenant": tenant_id})
        return result.deleted_count > 0
