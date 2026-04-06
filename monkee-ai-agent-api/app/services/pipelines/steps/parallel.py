"""
parallel step — runs multiple sub-steps concurrently and aggregates results.

Step config:
  steps: list[PipelineStep]   sub-steps to run in parallel
  aggregate_template: str     optional — template to build a combined output
                              e.g. "Análise de fatos: {{steps.step_1.output}}\\n\\nTipificação: {{steps.step_2.output}}"
"""
import asyncio
import json
from collections.abc import AsyncIterator

from app.models.pipeline import PipelineStep
from app.services.agents.context import UserContext
from app.services.agents.runner import SSEEvent, _sse
from app.services.pipelines.context import StepContext, StepResult


async def run(
    step: PipelineStep,
    ctx: StepContext,
    user_ctx: UserContext,
    step_runner,   # callable: (sub_step, ctx, user_ctx) -> AsyncIterator[str]
) -> AsyncIterator[str]:
    sub_steps: list[dict] = step.config.get("steps", [])
    aggregate_template: str = step.config.get("aggregate_template", "")

    if not sub_steps:
        ctx.set_result(StepResult(step_id=step.id, step_name=step.name, status="completed"))
        return

    # Rebuild PipelineStep objects from config dicts
    from app.models.pipeline import PipelineStep as PS
    parsed_sub_steps = [PS(**s) for s in sub_steps]

    # Collect all SSE chunks from each sub-step concurrently
    # We buffer per-step to interleave safely over SSE
    queues: list[asyncio.Queue] = [asyncio.Queue() for _ in parsed_sub_steps]

    async def _drain_step(sub_step: PS, q: asyncio.Queue) -> None:
        async for chunk in step_runner(sub_step, ctx, user_ctx):
            await q.put(chunk)
        await q.put(None)   # sentinel

    tasks = [
        asyncio.create_task(_drain_step(ss, q))
        for ss, q in zip(parsed_sub_steps, queues)
    ]

    # Round-robin drain until all queues exhausted
    active = list(range(len(queues)))
    while active:
        for i in list(active):
            try:
                item = queues[i].get_nowait()
                if item is None:
                    active.remove(i)
                else:
                    yield item
            except asyncio.QueueEmpty:
                pass
        if active:
            await asyncio.sleep(0)   # yield control

    await asyncio.gather(*tasks, return_exceptions=True)

    # Build aggregated output
    if aggregate_template:
        combined = ctx.resolve(aggregate_template)
    else:
        parts = [
            f"### {s.name}\n{ctx.get_output(s.id)}"
            for s in parsed_sub_steps
        ]
        combined = "\n\n".join(parts)

    ctx.set_result(StepResult(
        step_id=step.id,
        step_name=step.name,
        status="completed",
        output=combined,
    ))
