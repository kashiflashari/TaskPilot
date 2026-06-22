"""The TaskPilot agent runtime.

A tool-calling loop that plans with a :class:`~taskpilot.planner.base.Planner`,
executes tools, persists state to memory, and enforces human-approval gates on
irreversible actions. When no synchronous approver is configured (manual mode),
the run pauses and returns a ``PENDING_APPROVAL`` result that can be resumed via
:meth:`TaskPilotAgent.resume` — surviving process restarts when backed by Redis.
"""

from __future__ import annotations

import uuid

from taskpilot.approvals import get_approver
from taskpilot.config import Settings, get_settings
from taskpilot.connectors import build_workspace
from taskpilot.memory import get_memory
from taskpilot.models import (
    ActionType,
    AgentAction,
    ApprovalRequest,
    RunStatus,
    WorkflowResult,
)
from taskpilot.planner import get_planner

_USE_SETTINGS = object()


class TaskPilotAgent:
    def __init__(
        self,
        settings: Settings | None = None,
        workspace=None,
        planner=None,
        memory=None,
        approver=_USE_SETTINGS,
    ) -> None:
        self.settings = settings or get_settings()
        self.workspace = workspace or build_workspace(self.settings)
        self.registry = self.workspace.registry
        self.planner = planner or get_planner(self.settings)
        self.memory = memory or get_memory(self.settings)
        self.approver = get_approver(self.settings) if approver is _USE_SETTINGS else approver

    # --- public API ------------------------------------------------------
    def run(self, goal: str, session_id: str | None = None) -> WorkflowResult:
        session_id = session_id or uuid.uuid4().hex[:12]
        session = {"goal": goal, "history": []}
        self.memory.save_session(session_id, session)
        return self._loop(session_id, session)

    def resume(self, approval_id: str, approved: bool) -> WorkflowResult:
        pending = self.memory.load_pending(approval_id)
        if not pending:
            return WorkflowResult(session_id="", status=RunStatus.ERROR,
                                  output=f"Unknown or expired approval id: {approval_id}")
        self.memory.delete_pending(approval_id)
        session_id = pending["session_id"]
        session = self.memory.load_session(session_id) or {"goal": "", "history": []}
        action = AgentAction(ActionType.TOOL_CALL, tool=pending["tool"], args=pending["args"])

        if not approved:
            session["history"].append(self._denied_entry(action))
            self.memory.save_session(session_id, session)
            return self._result(session_id, session, RunStatus.DENIED,
                                output=f"Action '{action.tool}' was denied.")

        self._execute(action, session)  # approval granted → run the gated tool
        self.memory.save_session(session_id, session)
        return self._loop(session_id, session)

    # --- internals -------------------------------------------------------
    def _loop(self, session_id: str, session: dict) -> WorkflowResult:
        goal, history = session["goal"], session["history"]
        for _ in range(self.settings.max_steps):
            action = self.planner.propose(goal, history, self.registry)

            if action.type == ActionType.FINAL:
                return self._result(session_id, session, RunStatus.COMPLETED, output=action.content)

            tool = self.registry.get(action.tool or "")
            if tool is None:
                history.append({"role": "tool", "tool": action.tool, "args": action.args,
                                "ok": False, "output": None, "error": f"unknown tool '{action.tool}'"})
                self.memory.save_session(session_id, session)
                continue

            if tool.requires_approval:
                decision = (
                    None if self.approver is None
                    else self.approver.approve(action, self._describe(action))
                )
                if decision is None:  # pause for external/human approval
                    request = self._make_pending(session_id, action)
                    self.memory.save_session(session_id, session)
                    return self._result(session_id, session, RunStatus.PENDING_APPROVAL,
                                        output="Awaiting human approval.", pending=request)
                if decision is False:
                    history.append(self._denied_entry(action))
                    self.memory.save_session(session_id, session)
                    return self._result(session_id, session, RunStatus.DENIED,
                                        output=f"Action '{action.tool}' was denied.")

            self._execute(action, session)
            self.memory.save_session(session_id, session)

        return self._result(session_id, session, RunStatus.MAX_STEPS,
                            output="Reached the maximum number of steps before completing.")

    def _execute(self, action: AgentAction, session: dict) -> None:
        result = self.registry.execute(action.tool, action.args)
        session["history"].append({
            "role": "tool", "tool": action.tool, "args": action.args,
            "ok": result.ok, "output": result.output, "error": result.error,
        })

    def _make_pending(self, session_id: str, action: AgentAction) -> ApprovalRequest:
        approval_id = uuid.uuid4().hex[:12]
        request = ApprovalRequest(
            approval_id=approval_id, session_id=session_id,
            tool=action.tool, args=action.args, description=self._describe(action),
        )
        self.memory.save_pending(approval_id, {
            "session_id": session_id, "tool": action.tool,
            "args": action.args, "description": request.description,
        })
        return request

    @staticmethod
    def _denied_entry(action: AgentAction) -> dict:
        return {"role": "tool", "tool": action.tool, "args": action.args,
                "ok": False, "output": None, "error": "denied by approver"}

    @staticmethod
    def _describe(action: AgentAction) -> str:
        return f"Run '{action.tool}' with arguments {action.args}"

    @staticmethod
    def _result(session_id, session, status, output="", pending=None) -> WorkflowResult:
        steps = [
            {"type": "tool_call", "tool": h["tool"], "args": h.get("args", {}),
             "ok": h.get("ok"), "output": h.get("output"), "error": h.get("error")}
            for h in session["history"] if h.get("role") == "tool"
        ]
        return WorkflowResult(session_id=session_id, status=status, output=output,
                              steps=steps, pending_approval=pending)
