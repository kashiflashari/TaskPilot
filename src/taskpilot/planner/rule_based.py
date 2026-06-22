"""A deterministic, offline rule-based planner.

This drives a few canonical multi-step workflows without an LLM, so TaskPilot
runs end-to-end (including the human-approval gate) with no API keys — for demos
and tests. Set ``LLM_PROVIDER=openai`` for open-ended, model-driven planning.
"""

from __future__ import annotations

import re

from taskpilot.models import ActionType, AgentAction
from taskpilot.planner.base import executed_tools, last_output_of
from taskpilot.registry import ToolRegistry

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_CHANNEL_RE = re.compile(r"#(\w+)")


def _channel(goal: str) -> str:
    m = _CHANNEL_RE.search(goal)
    if m:
        return m.group(1)
    for name in ("general", "random"):
        if name in goal.lower():
            return name
    return "general"


def _recipient(goal: str) -> str:
    m = _EMAIL_RE.search(goal)
    return m.group(0) if m else "me@example.com"


def _summarize_messages(messages) -> str:
    if not isinstance(messages, list):
        return "(no messages)"
    return "\n".join(f"- {m.get('user', '?')}: {m.get('text', '')}" for m in messages)


class RuleBasedPlanner:
    def propose(self, goal: str, history: list[dict], registry: ToolRegistry) -> AgentAction:
        g = goal.lower()
        done = executed_tools(history)
        wants_email = any(w in g for w in ("email", "gmail", "mail"))

        # Workflow: read a Slack channel → email a summary.
        if "slack" in g and wants_email:
            channel = _channel(goal)
            if "slack_read_messages" not in done:
                return AgentAction(ActionType.TOOL_CALL, "slack_read_messages", {"channel": channel})
            if "gmail_send_email" not in done:
                body = _summarize_messages(last_output_of(history, "slack_read_messages"))
                return AgentAction(
                    ActionType.TOOL_CALL,
                    "gmail_send_email",
                    {
                        "to": _recipient(goal),
                        "subject": f"Summary of #{channel}",
                        "body": f"Summary of #{channel}:\n{body}",
                    },
                )
            return AgentAction(
                ActionType.FINAL,
                content=f"Emailed the #{channel} summary to {_recipient(goal)}.",
            )

        # Workflow: Notion search (then optionally create a page).
        if "notion" in g:
            query = goal.split("about")[-1].strip() if "about" in g else goal
            if "notion_search" not in done:
                return AgentAction(ActionType.TOOL_CALL, "notion_search", {"query": query[:60]})
            if "create" in g and "notion_create_page" not in done:
                return AgentAction(
                    ActionType.TOOL_CALL,
                    "notion_create_page",
                    {"title": query[:60] or "Untitled", "content": f"Created by TaskPilot for: {goal}"},
                )
            found = last_output_of(history, "notion_search")
            return AgentAction(ActionType.FINAL, content=f"Notion search complete. Found: {found}")

        # Workflow: triage unread email.
        if wants_email and ("unread" in g or "inbox" in g or "triage" in g):
            if "gmail_list_unread" not in done:
                return AgentAction(ActionType.TOOL_CALL, "gmail_list_unread", {})
            unread = last_output_of(history, "gmail_list_unread")
            return AgentAction(ActionType.FINAL, content=f"You have unread email: {unread}")

        return AgentAction(
            ActionType.FINAL,
            content=(
                "The offline rule-based planner doesn't recognise this request. "
                "Try a Slack→email summary, a Notion search/create, or email triage — "
                "or set LLM_PROVIDER=openai for open-ended planning. "
                f"Available tools:\n{registry.describe()}"
            ),
        )
