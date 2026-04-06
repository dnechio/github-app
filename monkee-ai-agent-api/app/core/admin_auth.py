from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.auth import TokenPayload, get_current_user

ADMIN_GROUP = "admin"


def require_admin(
    payload: Annotated[TokenPayload, Depends(get_current_user)],
) -> TokenPayload:
    """Dependency: ensures the caller belongs to the 'admin' group."""
    if ADMIN_GROUP not in payload.groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return payload
