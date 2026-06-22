"""Runtime tests: approval gating, pause/resume, denial, and step caps."""

import json

from taskpilot.agent import TaskPilotAgent
from taskpilot.approvals import AutoApprover, DenyAllApprover
from taskpilot.models import ActionType, AgentAction, RunStatus
from taskpilot.planner.scripted import ScriptedPlanner

READ = AgentAction(ActionType.TOOL_CALL, "slack_read_messages", {"channel": "general"})
SEND = AgentAction(ActionType.TOOL_CALL, "gmail_send_email",
                   {"to": "boss@corp.com", "subject": "S", "body": "B"})
DONE = AgentAction(ActionType.FINAL, content="all done")


def _agent(settings, workspace, store, approver, actions):
    return TaskPilotAgent(
        settings, workspace=workspace, planner=ScriptedPlanner(actions), memory=store,
        approver=approver,
    )


def test_auto_approval_runs_gated_tool(settings, workspace, store):
    agent = _agent(settings, workspace, store, AutoApprover(), [READ, SEND, DONE])
    result = agent.run("demo")
    assert result.status == RunStatus.COMPLETED
    assert workspace.gmail.sent[-1]["to"] == "boss@corp.com"
    assert [s["tool"] for s in result.steps] == ["slack_read_messages", "gmail_send_email"]


def test_manual_mode_pauses_before_irreversible_action(settings, workspace, store):
    agent = _agent(settings, workspace, store, None, [READ, SEND, DONE])
    result = agent.run("demo", session_id="sess1")
    assert result.status == RunStatus.PENDING_APPROVAL
    assert result.pending_approval.tool == "gmail_send_email"
    # The gated action has NOT run yet.
    assert workspace.gmail.sent == []
    # The read step already happened and is recorded.
    assert result.steps[0]["tool"] == "slack_read_messages"


def test_resume_with_approval_completes(settings, workspace, store):
    agent = _agent(settings, workspace, store, None, [READ, SEND, DONE])
    pending = agent.run("demo").pending_approval
    result = agent.resume(pending.approval_id, approved=True)
    assert result.status == RunStatus.COMPLETED
    assert workspace.gmail.sent[-1]["to"] == "boss@corp.com"


def test_resume_with_denial_blocks_action(settings, workspace, store):
    agent = _agent(settings, workspace, store, None, [READ, SEND, DONE])
    pending = agent.run("demo").pending_approval
    result = agent.resume(pending.approval_id, approved=False)
    assert result.status == RunStatus.DENIED
    assert workspace.gmail.sent == []


def test_deny_all_approver_blocks_inline(settings, workspace, store):
    agent = _agent(settings, workspace, store, DenyAllApprover(), [READ, SEND, DONE])
    result = agent.run("demo")
    assert result.status == RunStatus.DENIED
    assert workspace.gmail.sent == []


def test_max_steps_cap(settings, workspace, store):
    settings.max_steps = 3
    agent = _agent(settings, workspace, store, AutoApprover(), [READ, READ, READ, READ, READ])
    result = agent.run("loop")
    assert result.status == RunStatus.MAX_STEPS
    assert len(result.steps) == 3


def test_unknown_approval_id_is_handled(settings, workspace, store):
    agent = _agent(settings, workspace, store, None, [DONE])
    result = agent.resume("nonexistent", approved=True)
    assert result.status == RunStatus.ERROR


def test_result_is_json_serialisable(settings, workspace, store):
    agent = _agent(settings, workspace, store, AutoApprover(), [READ, DONE])
    json.dumps(agent.run("demo").to_dict())  # must not raise
