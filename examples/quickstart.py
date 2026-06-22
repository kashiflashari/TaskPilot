"""Quickstart: run a multi-step workflow with a human-approval gate.

    python examples/quickstart.py

Runs fully offline (rule-based planner + mock Slack/Gmail/Notion). Demonstrates
the pause-on-irreversible-action flow and how to resume after approval.
"""

from taskpilot.agent import TaskPilotAgent
from taskpilot.config import Settings

GOAL = "Summarise #general on Slack and email it to boss@corp.com"


def main() -> None:
    settings = Settings(_env_file=None, approval_mode="manual")  # offline + manual gate
    agent = TaskPilotAgent(settings)

    print(f"Goal: {GOAL}\n")
    result = agent.run(GOAL)

    if result.status.value == "pending_approval":
        req = result.pending_approval
        print(f"Steps so far: {[s['tool'] for s in result.steps]}")
        print(f"\nPaused for approval -> {req.description}")
        print("Approving…\n")
        result = agent.resume(req.approval_id, approved=True)

    print(f"Status: {result.status.value}")
    for s in result.steps:
        print(f"  - {s['tool']}: {'ok' if s['ok'] else s['error']}")
    print(f"\n{result.output}")


if __name__ == "__main__":
    main()
