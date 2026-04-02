from pydantic import BaseModel
from agno.agent import Agent

from app.models.agent import AgentConfig
from app.services.agents.models import ROUTER_MODEL


class RoutingDecision(BaseModel):
    target_type: str   # "agent" | "pipeline"
    target_id: str
    target_name: str
    reason: str


class RouterAgentService:
    """
    Wraps the Agno RouterAgent.

    In LLM mode: uses a lightweight model (Gemini Flash) to semantically
    match the user message against agent routing_descriptions.

    In rules mode: applies regex patterns before falling back to LLM.
    """

    def __init__(self, agents: list[AgentConfig], fallback_id: str | None = None):
        self._agents = agents
        self._fallback_id = fallback_id
        self._agent = self._build()

    def _build(self) -> Agent:
        candidates = "\n".join(
            f"- id={a.id} name={a.name!r}: {a.routing_description}"
            for a in self._agents
            if a.enabled
        )

        return Agent(
            name="RouterAgent",
            model=ROUTER_MODEL(),
            instructions=f"""
Você é um roteador inteligente de agentes jurídicos.
Analise a mensagem do usuário e escolha o agente mais adequado.

Agentes disponíveis:
{candidates}

Responda SOMENTE com JSON no formato:
{{"target_type": "agent", "target_id": "<id>", "target_name": "<name>", "reason": "<motivo breve>"}}
""",
            response_model=RoutingDecision,
            structured_outputs=True,
        )

    async def route(self, message: str) -> RoutingDecision:
        response = await self._agent.arun(message)
        decision: RoutingDecision = response.content

        # Validate target exists; fall back if not
        valid_ids = {a.id for a in self._agents}
        if decision.target_id not in valid_ids:
            fallback = self._fallback_id or (self._agents[0].id if self._agents else None)
            return RoutingDecision(
                target_type="agent",
                target_id=fallback or "",
                target_name="fallback",
                reason="Router returned unknown id — using fallback",
            )

        return decision
