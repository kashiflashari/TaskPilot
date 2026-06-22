"""Planner protocol and small helpers for reading run history."""

from __future__ import annotations

from typing import Any, Protocol

from taskpilot.models import AgentAction
from taskpilot.registry import ToolRegistry


class Planner(Protocol):
    def propose(self, goal: str, history: list[dict], registry: ToolRegistry) -> AgentAction:
        """Return the next action to take given the goal so far."""
        ...


def executed_tools(history: list[dict]) -> list[str]:
    """Names of tools that have already run (in order)."""
    return [h["tool"] for h in history if h.get("role") == "tool" and h.get("tool")]


def last_output_of(history: list[dict], tool_name: str) -> Any:
    """The most recent output recorded for ``tool_name``, or ``None``."""
    for h in reversed(history):
        if h.get("role") == "tool" and h.get("tool") == tool_name:
            return h.get("output")
    return None
