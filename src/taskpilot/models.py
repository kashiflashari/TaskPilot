"""Core data structures for the agent runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class ActionType(str, Enum):
    TOOL_CALL = "tool_call"
    FINAL = "final"


@dataclass
class Tool:
    """A callable capability exposed to the agent.

    ``requires_approval`` marks irreversible / outward-facing actions (sending an
    email, posting a message, creating a page) that must pass a human-approval
    gate before execution.
    """

    name: str
    description: str
    parameters: dict  # JSON-schema-style {name: {type, description}}
    func: Callable[..., Any]
    requires_approval: bool = False

    def to_openai_schema(self) -> dict:
        props = {
            k: {"type": v.get("type", "string"), "description": v.get("description", "")}
            for k, v in self.parameters.items()
        }
        required = [k for k, v in self.parameters.items() if v.get("required", True)]
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {"type": "object", "properties": props, "required": required},
            },
        }


@dataclass
class AgentAction:
    """What the planner decides to do next."""

    type: ActionType
    tool: str | None = None
    args: dict = field(default_factory=dict)
    content: str = ""  # final answer, or the planner's reasoning note


@dataclass
class ToolResult:
    tool: str
    args: dict
    ok: bool
    output: Any = None
    error: str | None = None


class RunStatus(str, Enum):
    COMPLETED = "completed"
    PENDING_APPROVAL = "pending_approval"
    DENIED = "denied"
    MAX_STEPS = "max_steps"
    ERROR = "error"


@dataclass
class ApprovalRequest:
    approval_id: str
    session_id: str
    tool: str
    args: dict
    description: str


@dataclass
class WorkflowResult:
    session_id: str
    status: RunStatus
    output: str = ""
    steps: list[dict] = field(default_factory=list)  # serialized transcript entries
    pending_approval: ApprovalRequest | None = None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "output": self.output,
            "steps": self.steps,
            "pending_approval": (
                {
                    "approval_id": self.pending_approval.approval_id,
                    "tool": self.pending_approval.tool,
                    "args": self.pending_approval.args,
                    "description": self.pending_approval.description,
                }
                if self.pending_approval
                else None
            ),
        }
