"""Gmail connector (mock for local dev/tests; MCP server in production)."""

from __future__ import annotations

from taskpilot.models import Tool


class MockGmail:
    def __init__(self) -> None:
        self.inbox: list[dict] = [
            {
                "id": "m1",
                "from": "ci@build.example",
                "subject": "Nightly build report",
                "body": "All 312 tests passed. Coverage 87%.",
                "unread": True,
            },
            {
                "id": "m2",
                "from": "pm@team.example",
                "subject": "Roadmap sync",
                "body": "Can we move the Q3 planning review to Thursday?",
                "unread": True,
            },
        ]
        self.sent: list[dict] = []

    def list_unread(self) -> list[dict]:
        return [{k: m[k] for k in ("id", "from", "subject")} for m in self.inbox if m["unread"]]

    def read_email(self, message_id: str) -> dict:
        for m in self.inbox:
            if m["id"] == message_id:
                m["unread"] = False
                return m
        return {"error": f"no message {message_id}"}

    def send_email(self, to: str, subject: str, body: str) -> dict:
        msg = {"to": to, "subject": subject, "body": body}
        self.sent.append(msg)
        return {"ok": True, **msg}


def gmail_tools(conn: MockGmail) -> list[Tool]:
    return [
        Tool(
            name="gmail_list_unread",
            description="List unread emails (id, sender, subject).",
            parameters={},
            func=lambda: conn.list_unread(),
        ),
        Tool(
            name="gmail_read_email",
            description="Read the full body of an email by id and mark it read.",
            parameters={"message_id": {"type": "string", "description": "Email id, e.g. 'm1'"}},
            func=lambda message_id: conn.read_email(message_id),
        ),
        Tool(
            name="gmail_send_email",
            description="Send an email.",
            parameters={
                "to": {"type": "string", "description": "Recipient address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body"},
            },
            func=lambda to, subject, body: conn.send_email(to, subject, body),
            requires_approval=True,
        ),
    ]
