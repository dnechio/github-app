"""
StepContext — carries state across all steps of a pipeline execution.

  - user_params: params filled by user before the pipeline starts
  - results: map of step_id → StepResult, populated as steps complete
  - Template resolution: {{params.key}}, {{steps.step_id.output}}, {{steps.step_id.output.field}}
"""
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepResult:
    step_id: str
    step_name: str
    status: str = "pending"       # pending | running | completed | failed | skipped
    output: str = ""              # primary text output (used by downstream agents)
    output_data: dict = field(default_factory=dict)   # structured output (tool results, etc.)
    error: str | None = None


@dataclass
class StepContext:
    execution_id: str
    pipeline_id: str
    user_params: dict[str, Any]
    results: dict[str, StepResult] = field(default_factory=dict)

    def set_result(self, result: StepResult) -> None:
        self.results[result.step_id] = result

    def get_output(self, step_id: str) -> str:
        r = self.results.get(step_id)
        return r.output if r else ""

    def resolve(self, text: str) -> str:
        """
        Replaces placeholders in a string:
          {{params.key}}              → user_params["key"]
          {{steps.step_id.output}}    → results[step_id].output
          {{steps.step_id.field}}     → results[step_id].output_data["field"]
        """
        def _replace(match: re.Match) -> str:
            expr = match.group(1).strip()
            parts = expr.split(".")
            try:
                if parts[0] == "params" and len(parts) == 2:
                    return str(self.user_params.get(parts[1], ""))
                if parts[0] == "steps" and len(parts) >= 3:
                    result = self.results.get(parts[1])
                    if not result:
                        return ""
                    if parts[2] == "output":
                        if len(parts) == 3:
                            return result.output
                        # nested field: {{steps.id.output.field}}
                        return str(result.output_data.get(parts[3], ""))
                    return str(result.output_data.get(parts[2], ""))
            except (IndexError, KeyError):
                pass
            return match.group(0)   # leave unresolved placeholders as-is

        return re.sub(r"\{\{([^}]+)\}\}", _replace, text)

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "pipeline_id": self.pipeline_id,
            "user_params": self.user_params,
            "results": {k: v.__dict__ for k, v in self.results.items()},
        }
