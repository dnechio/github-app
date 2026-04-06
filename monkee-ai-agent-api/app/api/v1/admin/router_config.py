from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.admin_auth import require_admin
from app.core.auth import TokenPayload
from app.core.database import get_db
from app.models.router_config import RouterConfig

router = APIRouter(prefix="/admin/router", tags=["admin:router"])

Tenant = Annotated[TokenPayload, Depends(require_admin)]

COLLECTION = "router_configs"


@router.get("/")
async def get_router_config(payload: Tenant):
    db = get_db()
    doc = await db[COLLECTION].find_one({"tenant": payload.tenant})
    if not doc:
        return RouterConfig(tenant=payload.tenant)
    return RouterConfig(**{**doc, "id": str(doc["_id"])})


@router.put("/")
async def upsert_router_config(body: RouterConfig, payload: Tenant):
    db = get_db()
    data = body.model_dump(exclude={"id"})
    data["tenant"] = payload.tenant
    await db[COLLECTION].replace_one({"tenant": payload.tenant}, data, upsert=True)
    return {"status": "updated"}


@router.post("/test")
async def test_routing(payload: Tenant, message: str):
    """
    Runs the RouterAgent against the current config and returns the routing decision
    without executing the target agent. Useful for admin validation.
    """
    from app.repositories.agent_repository import AgentRepository
    from app.services.agents.router_agent import RouterAgentService

    agent_repo = AgentRepository()
    available = await agent_repo.list_for_tenant(payload.tenant)
    if not available:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No agents configured")

    svc = RouterAgentService(agents=available)
    decision = await svc.route(message)
    return decision
