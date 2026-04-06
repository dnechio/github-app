import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from pydantic import BaseModel

from app.core.auth import create_session_token
from app.core.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
basic_scheme = HTTPBasic()


class SessionRequest(BaseModel):
    api_key: str


class SessionResponse(BaseModel):
    token: str
    expires_in: int   # seconds


@router.post("/session", response_model=SessionResponse)
async def create_session(body: SessionRequest):
    """
    Exchanges an API key (SHA-256 matched against DB) for a short-lived JWT.
    The JWT is then used in all subsequent requests.
    """
    db = get_db()
    api_key_hash = hashlib.sha256(body.api_key.encode()).hexdigest()

    user = await db["users"].find_one({"api_key_hash": api_key_hash, "enabled": True})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    from app.core.config import settings

    token = create_session_token(
        user_id=str(user["_id"]),
        tenant_id=user["tenant"],
        groups=user.get("groups", []),
    )

    return SessionResponse(token=token, expires_in=settings.JWT_EXPIRE_HOURS * 3600)
