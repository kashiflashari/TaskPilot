"""A planner that replays a fixed list of actions — used for deterministic tests."""

from __future__ import annotations

from taskpilot.models import ActionType, AgentAction
from taskpilot.registry import ToolRegistry


class ScriptedPlanner:
    def __init__(self, actions: list[AgentAction]) -> None:
        self._actions = list(actions)
        self._i = 0

    def propose(self, goal: str, history: list[dict], registry: ToolRegistry) -> AgentAction:
        if self._i < len(self._actions):
            action = self._actions[self._i]
            self._i += 1
            return action
        return AgentAction(type=ActionType.FINAL, content="done")
