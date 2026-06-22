"""Slack connector.

A mock, in-memory Slack used for local development and tests. In production the
same capabilities are provided by a Slack MCP server (see ``mcp_provider``).
"""

from __future__ import annotations

from taskpilot.models import Tool


class MockSlack:
    def __init__(self) -> None:
        self.channels: dict[str, list[dict]] = {
            "general": [
                {"user": "alice", "text": "Deploy to prod finished successfully."},
                {"user": "bob", "text": "Can someone review PR #42 today?"},
                {"user": "alice", "text": "Standup moved to 10:30 tomorrow."},
            ],
            "random": [{"user": "carol", "text": "Anyone up for lunch at 1?"}],
        }
        self.posted: list[dict] = []

    def list_channels(self) -> list[str]:
        return list(self.channels)

    def read_messages(self, channel: str) -> list[dict]:
        return self.channels.get(channel, [])

    def post_message(self, channel: str, text: str) -> dict:
        msg = {"channel": channel, "text": text}
        self.posted.append(msg)
        self.channels.setdefault(channel, []).append({"user": "taskpilot", "text": text})
        return {"ok": True, **msg}


def slack_tools(conn: MockSlack) -> list[Tool]:
    return [
        Tool(
            name="slack_list_channels",
            description="List the Slack channels available to the bot.",
            parameters={},
            func=lambda: conn.list_channels(),
        ),
        Tool(
            name="slack_read_messages",
            description="Read the recent messages in a Slack channel.",
            parameters={"channel": {"type": "string", "description": "Channel name, e.g. 'general'"}},
            func=lambda channel: conn.read_messages(channel),
        ),
        Tool(
            name="slack_post_message",
            description="Post a message to a Slack channel.",
            parameters={
                "channel": {"type": "string", "description": "Target channel name"},
                "text": {"type": "string", "description": "Message text to post"},
            },
            func=lambda channel, text: conn.post_message(channel, text),
            requires_approval=True,
        ),
    ]
