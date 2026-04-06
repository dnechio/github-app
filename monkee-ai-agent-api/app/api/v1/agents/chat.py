import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.auth import TokenPayload, build_user_context, get_current_user
from app.repositories.agent_repository import AgentRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.services.agents.builder import build_agent
from app.services.agents.router_agent import RouterAgentService
from app.services.agents.runner import AgentRunner

router = APIRouter(prefix="/agents", tags=["agents"])


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    agent_id: str | None = None   # None → RouterAgent selects


@router.post("/chat")
async def chat(
    body: ChatRequest,
    payload: Annotated[TokenPayload, Depends(get_current_user)],
):
    """
    SSE endpoint for agent chat.

    - If agent_id is provided, routes directly to that agent.
    - If agent_id is None, the RouterAgent selects the best agent automatically.
    """
    session_id = body.session_id or str(uuid.uuid4())
    user_ctx = build_user_context(payload, session_id)

    agent_repo = AgentRepository()
    kb_repo = KnowledgeBaseRepository()

    # --- Resolve target agent ---
    if body.agent_id:
        agent_config = await agent_repo.get_by_id(body.agent_id, payload.tenant)
        if not agent_config:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        routing_reason = ""
    else:
        available = await agent_repo.list_for_group(payload.tenant, payload.groups)
        if not available:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No agents available")

        router_svc = RouterAgentService(agents=available)
        decision = await router_svc.route(body.message)
        agent_config = next((a for a in available if a.id == decision.target_id), available[0])
        routing_reason = decision.reason

    # --- Check group access ---
    if agent_config.allowed_groups and not any(g in payload.groups for g in agent_config.allowed_groups):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for this agent")

    # --- Load linked KBs ---
    kb_configs = await kb_repo.get_by_ids(agent_config.knowledge_bases, payload.tenant)

    # --- Build agent and stream ---
    agent = build_agent(agent_config, user_ctx, kb_configs)
    runner = AgentRunner(agent)

    return StreamingResponse(
        runner.stream(body.message, agent_name=agent_config.name if routing_reason else ""),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Session-Id": session_id,
            "X-Agent-Id": agent_config.id,
        },
    )


@router.get("/")
async def list_agents(payload: Annotated[TokenPayload, Depends(get_current_user)]):
    """Returns agents accessible to the current user's groups."""
    repo = AgentRepository()
    agents = await repo.list_for_group(payload.tenant, payload.groups)
    return [
        {
            "id": a.id,
            "name": a.name,
            "slug": a.slug,
            "description": a.description,
            "routing_description": a.routing_description,
            "routing_tags": a.routing_tags,
            "model": a.model,
            "provider": a.provider,
        }
        for a in agents
    ]
