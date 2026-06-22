"""Connectors expose Slack / Gmail / Notion capabilities as agent tools.

Local development and tests use in-memory mock connectors. In production the
same capabilities come from MCP servers (added when ``MCP_CONFIG_PATH`` is set).
"""

from __future__ import annotations

from dataclasses import dataclass

from taskpilot.config import Settings
from taskpilot.connectors.gmail import MockGmail, gmail_tools
from taskpilot.connectors.notion import MockNotion, notion_tools
from taskpilot.connectors.slack import MockSlack, slack_tools
from taskpilot.registry import ToolRegistry

__all__ = ["Workspace", "build_workspace", "MockSlack", "MockGmail", "MockNotion"]


@dataclass
class Workspace:
    registry: ToolRegistry
    slack: MockSlack
    gmail: MockGmail
    notion: MockNotion


def build_workspace(settings: Settings) -> Workspace:
    slack, gmail, notion = MockSlack(), MockGmail(), MockNotion()
    registry = ToolRegistry()
    registry.add_all(slack_tools(slack))
    registry.add_all(gmail_tools(gmail))
    registry.add_all(notion_tools(notion))

    if settings.mcp_config_path:
        from taskpilot.mcp_provider import load_mcp_tools

        registry.add_all(load_mcp_tools(settings))

    return Workspace(registry=registry, slack=slack, gmail=gmail, notion=notion)
