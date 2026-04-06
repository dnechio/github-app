from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.services.agents.context import UserContext

bearer_scheme = HTTPBearer()


class TokenPayload(BaseModel):
    sub: str          # user_id
    tenant: str
    session: str
    groups: list[str] = []
    exp: datetime


def create_session_token(user_id: str, tenant_id: str, groups: list[str]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "tenant": tenant_id,
        "groups": groups,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _decode_token(token: str) -> TokenPayload:
    try:
        data = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return TokenPayload(**data)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> TokenPayload:
    return _decode_token(credentials.credentials)


def build_user_context(payload: TokenPayload, session_id: str) -> UserContext:
    return UserContext(
        user_id=payload.sub,
        tenant_id=payload.tenant,
        session_id=session_id,
        groups=payload.groups,
    )
