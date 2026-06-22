"""Planners decide the agent's next action given the goal, history, and tools."""

from taskpilot.planner.base import Planner, executed_tools, last_output_of
from taskpilot.planner.rule_based import RuleBasedPlanner
from taskpilot.planner.scripted import ScriptedPlanner


def get_planner(settings) -> Planner:
    provider = settings.llm_provider.lower()
    if provider == "openai":
        from taskpilot.planner.openai_planner import OpenAIPlanner

        return OpenAIPlanner(settings)
    return RuleBasedPlanner()


__all__ = [
    "Planner",
    "RuleBasedPlanner",
    "ScriptedPlanner",
    "get_planner",
    "executed_tools",
    "last_output_of",
]
