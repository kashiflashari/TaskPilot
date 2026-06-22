"""LLM planner backed by OpenAI tool-calling.

Re-plans each loop iteration: it shows the model the goal plus the progress so
far and lets it either call one tool or return a final answer. Compatible with
the OpenAI Agents SDK's function-tool schema (``registry.openai_schema()``).
"""

from __future__ import annotations

import json

from taskpilot.config import Settings
from taskpilot.models import ActionType, AgentAction
from taskpilot.registry import ToolRegistry

_SYSTEM = (
    "You are TaskPilot, an automation agent operating across Slack, Gmail, and Notion. "
    "Accomplish the user's goal by calling exactly ONE tool per step. Tools marked as "
    "requiring approval perform irreversible, outward-facing actions (sending email, "
    "posting messages, creating pages) — use them only when truly required; a human will "
    "be asked to approve them. When the goal is complete, stop calling tools and reply "
    "with a brief summary of what you did."
)


def _format_history(history: list[dict]) -> str:
    lines = []
    for h in history:
        if h.get("role") == "tool":
            lines.append(f"{h['tool']}({json.dumps(h.get('args', {}))}) -> {h.get('output')!r}")
    return "\n".join(lines) or "(nothing done yet)"


class OpenAIPlanner:  # pragma: no cover - requires OpenAI API
    def __init__(self, settings: Settings) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model
        self._temperature = settings.temperature

    def propose(self, goal: str, history: list[dict], registry: ToolRegistry) -> AgentAction:
        messages = [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": f"Goal: {goal}"},
            {
                "role": "user",
                "content": (
                    f"Progress so far:\n{_format_history(history)}\n\n"
                    "Decide the next single action, or give a final summary if done."
                ),
            },
        ]
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=registry.openai_schema(),
            temperature=self._temperature,
        )
        message = response.choices[0].message
        if message.tool_calls:
            call = message.tool_calls[0]
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            return AgentAction(ActionType.TOOL_CALL, tool=call.function.name, args=args)
        return AgentAction(ActionType.FINAL, content=message.content or "Done.")
