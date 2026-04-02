"""
transform step — reshapes data between steps without calling an LLM.

Step config:
  template: str         text template with {{placeholders}} — output is the resolved string
  extract_json_field: str   optional — if set, parses the previous step's output as JSON
                            and extracts this field into the step output
  source_step_id: str   optional — which step's output to use as source (defaults to last step)
"""
from app.models.pipeline import PipelineStep
from app.services.agents.context import UserContext
from app.services.pipelines.context import StepContext, StepResult


def run(
    step: PipelineStep,
    ctx: StepContext,
) -> StepResult:
    template: str = step.config.get("template", "")
    extract_field: str | None = step.config.get("extract_json_field")
    source_step_id: str | None = step.config.get("source_step_id")

    if template:
        output = ctx.resolve(template)

    elif extract_field and source_step_id:
        import json
        raw = ctx.get_output(source_step_id)
        try:
            data = json.loads(raw)
            output = str(data.get(extract_field, raw))
        except (json.JSONDecodeError, AttributeError):
            output = raw

    else:
        output = ""

    result = StepResult(
        step_id=step.id,
        step_name=step.name,
        status="completed",
        output=output,
    )
    ctx.set_result(result)
    return result


def run_file_input(step: PipelineStep, ctx: StepContext) -> StepResult:
    """
    file_input / user_input steps don't run logic here.
    They signal the executor to PAUSE and wait for the client to supply the value.
    The pause payload is stored as the step output once resumed.
    """
    result = StepResult(
        step_id=step.id,
        step_name=step.name,
        status="pending",
        output_data={"waiting_for": step.type, "prompt": step.config.get("prompt", "")},
    )
    ctx.set_result(result)
    return result
