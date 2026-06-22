"""A registry of tools available to the agent."""

from __future__ import annotations

from taskpilot.models import Tool, ToolResult


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def add(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def add_all(self, tools: list[Tool]) -> None:
        for t in tools:
            self.add(t)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list(self) -> list[Tool]:
        return list(self._tools.values())

    def names(self) -> list[str]:
        return list(self._tools)

    def openai_schema(self) -> list[dict]:
        return [t.to_openai_schema() for t in self._tools.values()]

    def describe(self) -> str:
        """Human/LLM-readable catalogue used in planner prompts."""
        lines = []
        for t in self._tools.values():
            params = ", ".join(t.parameters) or "—"
            gate = "  [requires approval]" if t.requires_approval else ""
            lines.append(f"- {t.name}({params}): {t.description}{gate}")
        return "\n".join(lines)

    def execute(self, name: str, args: dict) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(tool=name, args=args, ok=False, error=f"unknown tool '{name}'")
        try:
            output = tool.func(**args)
            return ToolResult(tool=name, args=args, ok=True, output=output)
        except TypeError as exc:
            return ToolResult(tool=name, args=args, ok=False, error=f"bad arguments: {exc}")
        except Exception as exc:  # pragma: no cover - connector failures
            return ToolResult(tool=name, args=args, ok=False, error=str(exc))
