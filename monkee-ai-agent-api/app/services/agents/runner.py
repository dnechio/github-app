import json
from collections.abc import AsyncIterator
from typing import Any

from agno.agent import Agent
from agno.models.response import ToolCall
from loguru import logger


class SSEEvent:
    """Helper to format SSE payloads consistently."""

    @staticmethod
    def text_delta(content: str) -> str:
        return _sse({"type": "text_delta", "content": content})

    @staticmethod
    def tool_call_start(name: str, params: dict) -> str:
        return _sse({"type": "tool_call_start", "name": name, "params": params})

    @staticmethod
    def tool_call_result(name: str, result: Any) -> str:
        return _sse({"type": "tool_call_result", "name": name, "result": str(result)})

    @staticmethod
    def agent_switch(agent_name: str, reason: str = "") -> str:
        return _sse({"type": "agent_switch", "agent": agent_name, "reason": reason})

    @staticmethod
    def memory_loaded(summaries: int) -> str:
        return _sse({"type": "memory_loaded", "summaries": summaries})

    @staticmethod
    def error(message: str, code: str = "internal_error") -> str:
        return _sse({"type": "error", "code": code, "message": message})

    @staticmethod
    def end() -> str:
        return _sse({"type": "end"})


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


class AgentRunner:
    """
    Runs an Agno Agent and streams the response as SSE events.

    Handles:
    - text streaming (text_delta)
    - tool call visibility (tool_call_start / tool_call_result)
    - memory loading notification (memory_loaded)
    - graceful error formatting (error + end)
    """

    def __init__(self, agent: Agent):
        self._agent = agent

    async def stream(self, message: str, agent_name: str = "") -> AsyncIterator[str]:
        logger.info(f"AgentRunner.stream | agent={self._agent.name} | msg={message[:80]!r}")

        try:
            # Notify if memory was pre-loaded into context
            if self._agent.memory:
                memories = getattr(self._agent.memory, "memories", [])
                if memories:
                    yield SSEEvent.memory_loaded(len(memories))

            if agent_name:
                yield SSEEvent.agent_switch(agent_name)

            # astream_response yields RunResponseChunk objects
            async for chunk in await self._agent.astream(message):
                # Text fragments
                if chunk.content:
                    yield SSEEvent.text_delta(chunk.content)

                # Tool call visibility
                if chunk.tools:
                    for tool in chunk.tools:
                        if isinstance(tool, ToolCall):
                            if tool.result is None:
                                yield SSEEvent.tool_call_start(
                                    tool.function.name,
                                    tool.function.arguments or {},
                                )
                            else:
                                yield SSEEvent.tool_call_result(
                                    tool.function.name,
                                    tool.result,
                                )

        except Exception as exc:
            logger.exception(f"AgentRunner error: {exc}")
            yield SSEEvent.error(str(exc))

        finally:
            yield SSEEvent.end()
