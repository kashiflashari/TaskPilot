"""Notion connector (mock for local dev/tests; MCP server in production)."""

from __future__ import annotations

from taskpilot.models import Tool


class MockNotion:
    def __init__(self) -> None:
        self.pages: dict[str, dict] = {
            "p1": {"id": "p1", "title": "Engineering Notes", "content": "Sprint 14 retro pending."},
            "p2": {"id": "p2", "title": "Meeting Log", "content": "2026-06-20: kickoff."},
        }
        self._next = 3

    def search(self, query: str) -> list[dict]:
        q = query.lower()
        return [
            {"id": p["id"], "title": p["title"]}
            for p in self.pages.values()
            if q in p["title"].lower() or q in p["content"].lower()
        ]

    def read_page(self, page_id: str) -> dict:
        return self.pages.get(page_id, {"error": f"no page {page_id}"})

    def create_page(self, title: str, content: str) -> dict:
        pid = f"p{self._next}"
        self._next += 1
        self.pages[pid] = {"id": pid, "title": title, "content": content}
        return {"ok": True, "id": pid, "title": title}

    def append_to_page(self, page_id: str, text: str) -> dict:
        page = self.pages.get(page_id)
        if not page:
            return {"error": f"no page {page_id}"}
        page["content"] += "\n" + text
        return {"ok": True, "id": page_id}


def notion_tools(conn: MockNotion) -> list[Tool]:
    return [
        Tool(
            name="notion_search",
            description="Search Notion pages by keyword.",
            parameters={"query": {"type": "string", "description": "Search query"}},
            func=lambda query: conn.search(query),
        ),
        Tool(
            name="notion_read_page",
            description="Read a Notion page by id.",
            parameters={"page_id": {"type": "string", "description": "Page id, e.g. 'p1'"}},
            func=lambda page_id: conn.read_page(page_id),
        ),
        Tool(
            name="notion_create_page",
            description="Create a new Notion page.",
            parameters={
                "title": {"type": "string", "description": "Page title"},
                "content": {"type": "string", "description": "Initial page content"},
            },
            func=lambda title, content: conn.create_page(title, content),
            requires_approval=True,
        ),
        Tool(
            name="notion_append",
            description="Append text to an existing Notion page.",
            parameters={
                "page_id": {"type": "string", "description": "Target page id"},
                "text": {"type": "string", "description": "Text to append"},
            },
            func=lambda page_id, text: conn.append_to_page(page_id, text),
            requires_approval=True,
        ),
    ]
