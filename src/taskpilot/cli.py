"""TaskPilot CLI:  run a workflow goal, approving irreversible steps inline.

    taskpilot run "Summarise #general on Slack and email it to me@corp.com"
    taskpilot run "..." --auto      # approve everything (trusted automation)
    taskpilot tools                 # list available tools
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from taskpilot.agent import TaskPilotAgent
from taskpilot.approvals import AutoApprover, CallbackApprover
from taskpilot.config import get_settings
from taskpilot.models import AgentAction, RunStatus


def _prompt_approver(action: AgentAction, description: str) -> bool:
    print(f"\n[!] Approval required: {description}", file=sys.stderr)
    reply = input("    Approve this action? [y/N] ").strip().lower()
    return reply in ("y", "yes")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="taskpilot", description="Agentic workflow automation bot.")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Run a workflow goal.")
    p_run.add_argument("goal")
    p_run.add_argument("--auto", action="store_true", help="Auto-approve irreversible actions.")

    sub.add_parser("tools", help="List available tools.")

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    settings = get_settings()

    if args.command == "tools":
        agent = TaskPilotAgent(settings)
        for t in agent.registry.list():
            gate = "  [approval]" if t.requires_approval else ""
            print(f"{t.name}{gate}\n    {t.description}")
        return 0

    if args.command == "run":
        approver = AutoApprover() if args.auto else CallbackApprover(_prompt_approver)
        agent = TaskPilotAgent(settings, approver=approver)
        result = agent.run(args.goal)
        print(f"\nStatus: {result.status.value}")
        for step in result.steps:
            mark = "[ok]" if step["ok"] else "[x]"
            print(f"  {mark} {step['tool']}({json.dumps(step['args'])})")
            if step.get("error"):
                print(f"      error: {step['error']}")
        print(f"\n{result.output}")
        return 0 if result.status == RunStatus.COMPLETED else 1

    parser.print_help(sys.stderr)
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
