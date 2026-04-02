from agno.agent import Agent

from app.models.agent import AgentConfig
from app.models.knowledge_base import KnowledgeBase
from app.services.agents.context import UserContext
from app.services.agents.models import resolve_model
from app.services.knowledge_bases.builder import build_knowledge
from app.services.memory.builder import build_memory


def _resolve_placeholders(text: str, user_ctx: UserContext) -> str:
    """Replaces {{user_id}}, {{tenant_id}}, {{session_id}} in instructions."""
    return (
        text.replace("{{user_id}}", user_ctx.user_id)
            .replace("{{tenant_id}}", user_ctx.tenant_id)
            .replace("{{session_id}}", user_ctx.session_id)
    )


def build_agent(
    config: AgentConfig,
    user_ctx: UserContext,
    kb_configs: list[KnowledgeBase] | None = None,
) -> Agent:
    """
    Builds an Agno Agent dynamically from an AgentConfig + UserContext.
    All behaviour is config-driven — no hardcoded prompts or models here.
    """
    model = resolve_model(
        config.provider,
        config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    knowledge = build_knowledge(
        kb_configs=kb_configs or [],
        user_ctx=user_ctx,
        can_use_user_files=config.can_use_user_files,
    )

    memory = build_memory(user_ctx) if config.can_use_memory else None

    instructions = _resolve_placeholders(config.instructions, user_ctx)

    # Inject user preferences from memory profile if available
    if user_ctx.preferences:
        prefs_text = "\n".join(f"- {k}: {v}" for k, v in user_ctx.preferences.items())
        instructions = f"{instructions}\n\n## Perfil do usuário\n{prefs_text}"

    return Agent(
        agent_id=config.id,
        name=config.name,
        model=model,
        instructions=instructions,
        knowledge=knowledge,
        memory=memory,
        add_history_to_messages=True,
        num_history_responses=10,
        show_tool_calls=True,
        markdown=True,
        # Citations shown only when KB is attached
        add_references=bool(knowledge) and config.show_citations,
        # Session scoped to (session_id, user_id) for history isolation
        session_id=user_ctx.session_id,
        user_id=user_ctx.user_id,
    )
