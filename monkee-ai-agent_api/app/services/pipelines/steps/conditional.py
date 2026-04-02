"""
conditional step — evaluates an expression and selects one of two branch step IDs.

Step config:
  condition: str        expression referencing ctx — e.g. "{{steps.step_1.output}}" contains "habeas corpus"
  if_true_step_id: str  ID of the step to run next when condition is truthy
  if_false_step_id: str ID of the step to run next when condition is falsy

The executor uses the returned next_step_id to decide which step to jump to.
"""
from app.models.pipeline import PipelineStep
from app.services.agents.context import UserContext
from app.services.pipelines.context import StepContext, StepResult


def evaluate(
    step: PipelineStep,
    ctx: StepContext,
) -> str | None:
    """
    Evaluates the condition and returns the ID of the next step to execute.
    Returns None if neither branch is configured (continue sequentially).
    """
    condition: str = step.config.get("condition", "")
    if_true: str | None = step.config.get("if_true_step_id")
    if_false: str | None = step.config.get("if_false_step_id")

    resolved = ctx.resolve(condition).strip()
    is_truthy = bool(resolved) and resolved.lower() not in ("false", "0", "none", "null", "")

    chosen = if_true if is_truthy else if_false

    ctx.set_result(StepResult(
        step_id=step.id,
        step_name=step.name,
        status="completed",
        output=f"condition={resolved!r} → {'true' if is_truthy else 'false'} → step={chosen}",
        output_data={"is_truthy": is_truthy, "next_step_id": chosen},
    ))

    return chosen
