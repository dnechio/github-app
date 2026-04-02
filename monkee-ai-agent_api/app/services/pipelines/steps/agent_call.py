"""
agent_call step — runs a single agent and collects its full output.

Step config:
  agent_id: str          required — which agent to call
  prompt_template: str   required — message sent to the agent (supports {{placeholders}})
  output_field: str      optional — if set, tries to parse JSON output and extract this field
"""
from collections.abc import AsyncIterator

from app.models.pipeline import PipelineStep
from app.repositories.agent_repository import AgentRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.services.agents.builder import build_agent
from app.services.agents.context import UserContext
from app.services.agents.runner import SSEEvent, _sse
from app.services.pipelines.context import StepContext, StepResult


async def run(
    step: PipelineStep,
    ctx: StepContext,
    user_ctx: UserContext,
) -> AsyncIterator[str]:
    """
    Yields SSE events while the agent runs, then yields step_complete.
    Returns via StepResult stored in ctx.
    """
    agent_id: str = step.config.get("agent_id", "")
    prompt_template: str = step.config.get("prompt_template", "")
    output_field: str | None = step.config.get("output_field")

    prompt = ctx.resolve(prompt_template)

    agent_repo = AgentRepository()
    kb_repo = KnowledgeBaseRepository()

    agent_config = await agent_repo.get_by_id(agent_id, user_ctx.tenant_id)
    if not agent_config:
        result = StepResult(
            step_id=step.id,
            step_name=step.name,
            status="failed",
            error=f"Agent {agent_id!r} not found",
        )
        ctx.set_result(result)
        yield SSEEvent.error(result.error, code="agent_not_found")
        return

    kb_configs = await kb_repo.get_by_ids(agent_config.knowledge_bases, user_ctx.tenant_id)
    agent = build_agent(agent_config, user_ctx, kb_configs)

    full_output = ""

    try:
        async for chunk in await agent.astream(prompt):
            if chunk.content:
                full_output += chunk.content
                yield SSEEvent.text_delta(chunk.content)

            if chunk.tools:
                from agno.models.response import ToolCall
                for tool in chunk.tools:
                    if isinstance(tool, ToolCall):
                        if tool.result is None:
                            yield SSEEvent.tool_call_start(
                                tool.function.name, tool.function.arguments or {}
                            )
                        else:
                            yield SSEEvent.tool_call_result(tool.function.name, tool.result)

    except Exception as exc:
        result = StepResult(
            step_id=step.id,
            step_name=step.name,
            status="failed",
            output=full_output,
            error=str(exc),
        )
        ctx.set_result(result)
        yield SSEEvent.error(str(exc))
        return

    # Extract structured field if requested
    output_data: dict = {}
    if output_field:
        import json
        try:
            parsed = json.loads(full_output)
            output_data[output_field] = parsed.get(output_field, parsed)
        except (json.JSONDecodeError, AttributeError):
            output_data[output_field] = full_output

    result = StepResult(
        step_id=step.id,
        step_name=step.name,
        status="completed",
        output=full_output,
        output_data=output_data,
    )
    ctx.set_result(result)
