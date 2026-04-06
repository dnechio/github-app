"""
PipelineExecutor — orchestrates a PipelineConfig step-by-step and streams SSE events.

Responsibilities:
  - Iterate steps in order, respecting conditional jumps
  - Delegate each step type to the appropriate handler
  - Persist execution state in MongoDB after every step
  - PAUSE on user_input / file_input steps and wait for the client to resume
  - Stream: step_start, text_delta, tool_call_*, step_complete, pipeline_paused, pipeline_complete, error

Usage:
  executor = PipelineExecutor(pipeline, execution, user_ctx)
  async for event in executor.run():
      yield event

  # After client supplies input:
  async for event in executor.resume(execution_id, resume_input):
      yield event
"""
import json
import uuid
from collections.abc import AsyncIterator
from datetime import datetime

from loguru import logger

from app.models.pipeline import PipelineConfig, PipelineExecution, PipelineStep
from app.repositories.pipeline_repository import PipelineRepository
from app.services.agents.context import UserContext
from app.services.agents.runner import _sse
from app.services.pipelines.context import StepContext, StepResult


# ── SSE event helpers ─────────────────────────────────────────────────────────

def _step_start(step: PipelineStep, step_index: int, total: int) -> str:
    return _sse({
        "type": "step_start",
        "step_id": step.id,
        "step_name": step.name,
        "step_type": step.type,
        "step_index": step_index,
        "total_steps": total,
    })


def _step_complete(step: PipelineStep, output_preview: str) -> str:
    return _sse({
        "type": "step_complete",
        "step_id": step.id,
        "step_name": step.name,
        "output_preview": output_preview[:200],
    })


def _pipeline_paused(step: PipelineStep, prompt: str) -> str:
    return _sse({
        "type": "pipeline_paused",
        "step_id": step.id,
        "step_type": step.type,   # "user_input" | "file_input"
        "prompt": prompt,
    })


def _pipeline_complete(execution_id: str) -> str:
    return _sse({"type": "pipeline_complete", "execution_id": execution_id})


def _pipeline_error(message: str, step_id: str | None = None) -> str:
    return _sse({"type": "error", "code": "pipeline_error", "message": message, "step_id": step_id})


# ── Executor ──────────────────────────────────────────────────────────────────

class PipelineExecutor:
    def __init__(
        self,
        pipeline: PipelineConfig,
        execution: PipelineExecution,
        user_ctx: UserContext,
    ):
        self._pipeline = pipeline
        self._execution = execution
        self._user_ctx = user_ctx
        self._repo = PipelineRepository()

        # Rebuild StepContext from persisted execution state
        self._ctx = StepContext(
            execution_id=execution.id,
            pipeline_id=pipeline.id,
            user_params=execution.user_params,
            results={
                r["step_id"]: StepResult(**r)
                for r in execution.steps_results
                if r.get("step_id")
            },
        )

    async def run(self) -> AsyncIterator[str]:
        """Run from current_step to completion (or first pause)."""
        steps = self._pipeline.steps
        total = len(steps)
        i = self._execution.current_step

        while i < total:
            step = steps[i]
            yield _step_start(step, i, total)

            # Pause steps
            if step.type in ("user_input", "file_input"):
                prompt = self._ctx.resolve(step.config.get("prompt", step.name))
                await self._persist(status="paused", current_step=i)
                yield _pipeline_paused(step, prompt)
                return  # client must call resume()

            # All other step types
            try:
                async for event in self._run_step(step, i):
                    yield event
            except Exception as exc:
                logger.exception(f"Pipeline {self._pipeline.id} step {step.id} failed: {exc}")
                await self._persist(status="failed", current_step=i)
                yield _pipeline_error(str(exc), step_id=step.id)
                return

            result = self._ctx.results.get(step.id)

            # Conditional jump
            if step.type == "conditional" and result:
                next_id = result.output_data.get("next_step_id")
                if next_id:
                    i = self._find_step_index(next_id, i)
                    await self._persist(status="running", current_step=i)
                    yield _step_complete(step, result.output)
                    continue

            yield _step_complete(step, result.output if result else "")
            i += 1
            await self._persist(status="running", current_step=i)

        await self._persist(status="completed", current_step=i)
        yield _pipeline_complete(self._execution.id)

    async def resume(self, resume_input: dict) -> AsyncIterator[str]:
        """
        Called after a user_input / file_input pause.

        resume_input keys:
          text: str        (for user_input)
          file_id: str     (for file_input)
        """
        if self._execution.status != "paused":
            yield _pipeline_error("Execution is not paused")
            return

        step = self._pipeline.steps[self._execution.current_step]

        # Record the user's input as the step output
        if step.type == "user_input":
            output = resume_input.get("text", "")
        else:  # file_input
            output = resume_input.get("file_id", "")

        result = StepResult(
            step_id=step.id,
            step_name=step.name,
            status="completed",
            output=output,
            output_data=resume_input,
        )
        self._ctx.set_result(result)

        # Advance past the pause step and continue
        self._execution.current_step += 1
        await self._persist(status="running", current_step=self._execution.current_step)

        yield _step_complete(step, output)
        async for event in self.run():
            yield event

    # ── Step dispatch ─────────────────────────────────────────────────────────

    async def _run_step(self, step: PipelineStep, index: int) -> AsyncIterator[str]:
        if step.type == "agent_call":
            from app.services.pipelines.steps.agent_call import run as agent_run
            async for event in agent_run(step, self._ctx, self._user_ctx):
                yield event

        elif step.type == "team_call":
            # Team call uses same interface as agent_call with a team_id
            from app.services.pipelines.steps.agent_call import run as agent_run
            async for event in agent_run(step, self._ctx, self._user_ctx):
                yield event

        elif step.type == "parallel":
            from app.services.pipelines.steps.parallel import run as parallel_run
            async for event in parallel_run(step, self._ctx, self._user_ctx, self._dispatch_sub_step):
                yield event

        elif step.type == "conditional":
            from app.services.pipelines.steps.conditional import evaluate
            evaluate(step, self._ctx)   # sets result in ctx, no SSE

        elif step.type == "transform":
            from app.services.pipelines.steps.transform import run as transform_run
            transform_run(step, self._ctx)   # sync, no SSE

        elif step.type == "tool_call":
            async for event in self._run_tool_step(step):
                yield event

        else:
            # Unknown step type — skip with a warning
            logger.warning(f"Unknown step type {step.type!r}, skipping")
            self._ctx.set_result(StepResult(
                step_id=step.id, step_name=step.name, status="skipped"
            ))

    async def _dispatch_sub_step(
        self, step: PipelineStep, ctx: StepContext, user_ctx: UserContext
    ) -> AsyncIterator[str]:
        """Passed to parallel runner so it can call back into the dispatcher."""
        async for event in self._run_step(step, -1):
            yield event

    async def _run_tool_step(self, step: PipelineStep) -> AsyncIterator[str]:
        """
        Executes a tool directly (without an agent wrapper).
        tool_name must be a registered tool class_name in the tools collection.
        """
        tool_name = step.config.get("tool_name", "")
        tool_params = {k: self._ctx.resolve(str(v)) for k, v in step.config.get("params", {}).items()}

        yield _sse({"type": "tool_call_start", "name": tool_name, "params": tool_params})

        try:
            result_text = await self._invoke_tool(tool_name, tool_params)
        except Exception as exc:
            self._ctx.set_result(StepResult(
                step_id=step.id, step_name=step.name, status="failed", error=str(exc)
            ))
            yield _sse({"type": "tool_call_result", "name": tool_name, "result": f"ERROR: {exc}"})
            raise

        self._ctx.set_result(StepResult(
            step_id=step.id,
            step_name=step.name,
            status="completed",
            output=result_text,
        ))
        yield _sse({"type": "tool_call_result", "name": tool_name, "result": result_text})

    async def _invoke_tool(self, tool_name: str, params: dict) -> str:
        """Placeholder — tools will be dynamically loaded from the registry."""
        # TODO: load ToolConfig from DB, instantiate the class, call it
        raise NotImplementedError(f"Tool {tool_name!r} not yet implemented in executor")

    # ── Persistence ───────────────────────────────────────────────────────────

    def _find_step_index(self, step_id: str, current: int) -> int:
        for i, s in enumerate(self._pipeline.steps):
            if s.id == step_id:
                return i
        logger.warning(f"Step ID {step_id!r} not found, continuing from {current + 1}")
        return current + 1

    async def _persist(self, status: str, current_step: int) -> None:
        self._execution.status = status
        self._execution.current_step = current_step
        self._execution.updated_at = datetime.utcnow()
        self._execution.steps_results = [
            r.__dict__ for r in self._ctx.results.values()
        ]
        await self._repo.update_execution(self._execution)


# ── Factory ───────────────────────────────────────────────────────────────────

async def create_execution(
    pipeline: PipelineConfig,
    user_ctx: UserContext,
    user_params: dict,
) -> PipelineExecution:
    repo = PipelineRepository()
    execution = PipelineExecution(
        id="",
        pipeline_id=pipeline.id,
        user_id=user_ctx.user_id,
        tenant=user_ctx.tenant_id,
        status="running",
        current_step=0,
        user_params=user_params,
    )
    exec_id = await repo.create_execution(execution)
    execution.id = exec_id
    return execution
