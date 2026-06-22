"""TaskPilot — an agentic workflow automation bot.

A tool-calling agent that executes multi-step workflows across Slack, Gmail, and
Notion (via MCP or direct connectors), with persistent memory and human-approval
gates before any irreversible action. See :class:`taskpilot.agent.TaskPilotAgent`.
"""

from taskpilot.config import Settings, get_settings

__version__ = "0.1.0"
__all__ = ["Settings", "get_settings", "__version__"]
