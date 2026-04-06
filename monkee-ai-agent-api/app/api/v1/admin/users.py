import hashlib
import secrets
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.core.admin_auth import require_admin
from app.core.auth import TokenPayload
from app.models.user import UserProfile, UserGroup
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/admin/users", tags=["admin:users"])

Tenant = Annotated[TokenPayload, Depends(require_admin)]


class UserCreateRequest(BaseModel):
    name: str
    email: str
    groups: list[str] = []
    enabled: bool = True
    day_limit_override: int | None = None
    week_limit_override: int | None = None
    month_limit_override: int | None = None


class UserUpdateRequest(UserCreateRequest):
    pass


class GroupCreateRequest(BaseModel):
    name: str
    description: str = ""


# ─── Users ────────────────────────────────────────────────────────────────────

@router.get("/")
async def list_users(payload: Tenant):
    repo = UserRepository()
    users = await repo.list_for_tenant(payload.tenant)
    # Never expose the api_key_hash in responses
    return [u.model_dump(exclude={"api_key_hash"}) for u in users]


@router.get("/{user_id}")
async def get_user(user_id: str, payload: Tenant):
    repo = UserRepository()
    user = await repo.get_by_id(user_id, payload.tenant)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user.model_dump(exclude={"api_key_hash"})


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(body: UserCreateRequest, payload: Tenant):
    """Creates a user and generates an API key. The raw key is returned ONCE — store it securely."""
    raw_key = secrets.token_urlsafe(32)
    profile = UserProfile(
        id="",
        tenant=payload.tenant,
        api_key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
        **body.model_dump(),
    )
    repo = UserRepository()
    new_id = await repo.upsert(profile)
    return {"id": new_id, "api_key": raw_key}  # raw key shown once only


@router.put("/{user_id}")
async def update_user(user_id: str, body: UserUpdateRequest, payload: Tenant):
    repo = UserRepository()
    existing = await repo.get_by_id(user_id, payload.tenant)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    updated = existing.model_copy(
        update={**body.model_dump(), "updated_at": datetime.utcnow()}
    )
    await repo.upsert(updated)
    return {"id": user_id}


@router.post("/{user_id}/rotate-key")
async def rotate_api_key(user_id: str, payload: Tenant):
    """Generates a new API key for the user. The raw key is returned ONCE."""
    new_raw_key = secrets.token_urlsafe(32)
    repo = UserRepository()
    ok = await repo.rotate_api_key(user_id, payload.tenant, new_raw_key)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"api_key": new_raw_key}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, payload: Tenant):
    repo = UserRepository()
    deleted = await repo.delete(user_id, payload.tenant)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


# ─── Groups ───────────────────────────────────────────────────────────────────

@router.get("/groups/")
async def list_groups(payload: Tenant):
    repo = UserRepository()
    return await repo.list_groups(payload.tenant)


@router.post("/groups/", status_code=status.HTTP_201_CREATED)
async def create_group(body: GroupCreateRequest, payload: Tenant):
    group = UserGroup(id="", tenant=payload.tenant, **body.model_dump())
    repo = UserRepository()
    new_id = await repo.upsert_group(group)
    return {"id": new_id}


@router.put("/groups/{group_id}")
async def update_group(group_id: str, body: GroupCreateRequest, payload: Tenant):
    group = UserGroup(id=group_id, tenant=payload.tenant, **body.model_dump())
    repo = UserRepository()
    await repo.upsert_group(group)
    return {"id": group_id}


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: str, payload: Tenant):
    repo = UserRepository()
    deleted = await repo.delete_group(group_id, payload.tenant)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
