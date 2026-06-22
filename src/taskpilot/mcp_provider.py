"""MCP (Model Context Protocol) tool provider.

Connects to one or more MCP servers (Slack / Gmail / Notion, etc.) described in a
JSON config and exposes their tools as TaskPilot :class:`Tool` objects. Sessions
are kept open on a background event loop so the synchronous agent runtime can call
async MCP tools transparently.

Config format (same shape as Claude/Cursor)::

    {
      "mcpServers": {
        "slack":  {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-slack"],
                   "env": {"SLACK_BOT_TOKEN": "..."}},
        "notion": {"command": "npx", "args": ["-y", "@notionhq/notion-mcp-server"],
                   "env": {"NOTION_API_KEY": "..."}}
      }
    }

Tools whose names imply a side effect (send/post/create/delete/update/append/…) are
flagged ``requires_approval`` so they pass through the human-approval gate.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from concurrent.futures import Future
from pathlib import Path

from taskpilot.config import Settings
from taskpilot.models import Tool

logger = logging.getLogger(__name__)

_APPROVAL_KEYWORDS = (
    "send", "post", "create", "delete", "update", "append", "write",
    "remove", "archive", "reply", "publish", "add", "move",
)


def _needs_approval(tool_name: str) -> bool:
    name = tool_name.lower()
    return any(kw in name for kw in _APPROVAL_KEYWORDS)


class MCPManager:  # pragma: no cover - requires live MCP servers
    """Owns a background asyncio loop and persistent MCP client sessions."""

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._sessions: dict[str, object] = {}
        self._stack = None

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _submit(self, coro) -> Future:
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def connect_all(self, servers: dict[str, dict]) -> list[Tool]:
        return self._submit(self._connect_all(servers)).result()

    async def _connect_all(self, servers: dict[str, dict]) -> list[Tool]:
        from contextlib import AsyncExitStack

        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        self._stack = AsyncExitStack()
        tools: list[Tool] = []
        for server_name, cfg in servers.items():
            params = StdioServerParameters(
                command=cfg["command"], args=cfg.get("args", []), env=cfg.get("env")
            )
            read, write = await self._stack.enter_async_context(stdio_client(params))
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self._sessions[server_name] = session
            listed = await session.list_tools()
            for mt in listed.tools:
                tools.append(self._wrap(server_name, mt))
        return tools

    def _wrap(self, server_name: str, mt) -> Tool:
        schema = getattr(mt, "inputSchema", None) or {}
        props = schema.get("properties", {}) if isinstance(schema, dict) else {}
        required = set(schema.get("required", [])) if isinstance(schema, dict) else set()
        parameters = {
            k: {
                "type": v.get("type", "string"),
                "description": v.get("description", ""),
                "required": k in required,
            }
            for k, v in props.items()
        }
        full_name = f"{server_name}__{mt.name}"

        def call(**kwargs):
            return self._submit(self._call(server_name, mt.name, kwargs)).result()

        return Tool(
            name=full_name,
            description=mt.description or f"{server_name} tool {mt.name}",
            parameters=parameters,
            func=call,
            requires_approval=_needs_approval(mt.name),
        )

    async def _call(self, server_name: str, tool_name: str, arguments: dict):
        session = self._sessions[server_name]
        result = await session.call_tool(tool_name, arguments=arguments)
        # Flatten text content blocks.
        parts = []
        for block in getattr(result, "content", []) or []:
            text = getattr(block, "text", None)
            parts.append(text if text is not None else str(block))
        return "\n".join(parts) if parts else getattr(result, "structuredContent", None)


def load_mcp_tools(settings: Settings) -> list[Tool]:
    path = Path(settings.mcp_config_path)
    if not path.exists():
        logger.warning("MCP config %s not found; no MCP tools loaded.", path)
        return []
    config = json.loads(path.read_text(encoding="utf-8"))
    servers = config.get("mcpServers", {})
    if not servers:
        return []
    try:  # pragma: no cover - requires live MCP servers
        manager = MCPManager()
        return manager.connect_all(servers)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to load MCP tools (%s).", exc)
        return []
