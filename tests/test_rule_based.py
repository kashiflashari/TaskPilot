"""End-to-end tests with the offline rule-based planner (no API keys)."""

from taskpilot.agent import TaskPilotAgent
from taskpilot.approvals import AutoApprover
from taskpilot.planner.rule_based import RuleBasedPlanner
from taskpilot.models import RunStatus

GOAL = "Summarise #general on Slack and email it to boss@corp.com"


def test_slack_to_email_workflow_auto(settings, workspace, store):
    agent = TaskPilotAgent(settings, workspace=workspace, planner=RuleBasedPlanner(),
                           memory=store, approver=AutoApprover())
    result = agent.run(GOAL)
    assert result.status == RunStatus.COMPLETED
    sent = workspace.gmail.sent[-1]
    assert sent["to"] == "boss@corp.com"
    assert "Deploy to prod" in sent["body"]  # summary contains the real Slack content
    tools_used = [s["tool"] for s in result.steps]
    assert tools_used == ["slack_read_messages", "gmail_send_email"]


def test_slack_to_email_pauses_then_resumes_across_agents(settings, workspace, store):
    # First agent pauses at the email step.
    agent1 = TaskPilotAgent(settings, workspace=workspace, planner=RuleBasedPlanner(),
                            memory=store, approver=None)
    paused = agent1.run(GOAL, session_id="s1")
    assert paused.status == RunStatus.PENDING_APPROVAL
    assert workspace.gmail.sent == []

    # A *fresh* agent (simulating a restart) resumes from shared memory.
    agent2 = TaskPilotAgent(settings, workspace=workspace, planner=RuleBasedPlanner(),
                            memory=store, approver=None)
    done = agent2.resume(paused.pending_approval.approval_id, approved=True)
    assert done.status == RunStatus.COMPLETED
    assert workspace.gmail.sent[-1]["to"] == "boss@corp.com"


def test_notion_search_workflow(settings, workspace, store):
    agent = TaskPilotAgent(settings, workspace=workspace, planner=RuleBasedPlanner(),
                           memory=store, approver=AutoApprover())
    result = agent.run("Search Notion about engineering")
    assert result.status == RunStatus.COMPLETED
    assert "notion_search" in [s["tool"] for s in result.steps]


def test_unrecognised_goal_finishes_without_side_effects(settings, workspace, store):
    agent = TaskPilotAgent(settings, workspace=workspace, planner=RuleBasedPlanner(),
                           memory=store, approver=AutoApprover())
    result = agent.run("Do something completely unrelated")
    assert result.status == RunStatus.COMPLETED
    assert result.steps == []
    assert workspace.gmail.sent == [] and workspace.slack.posted == []
