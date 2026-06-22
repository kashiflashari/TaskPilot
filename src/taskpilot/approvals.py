"""Human-approval gates for irreversible actions.

An :class:`Approver` decides whether an approval-gated tool call may proceed.
``AutoApprover`` / ``DenyAllApprover`` are non-interactive; ``CallbackApprover``
delegates to a function (e.g. a CLI prompt). The API uses ``None`` (no synchronous
approver) so it can pause and return a pending-approval response instead.
"""

from __future__ import annotations

from typing import Callable, Protocol

from taskpilot.config import Settings
from taskpilot.models import AgentAction


class Approver(Protocol):
    def approve(self, action: AgentAction, description: str) -> bool: ...


class AutoApprover:
    def approve(self, action: AgentAction, description: str) -> bool:
        return True


class DenyAllApprover:
    def approve(self, action: AgentAction, description: str) -> bool:
        return False


class CallbackApprover:
    def __init__(self, callback: Callable[[AgentAction, str], bool]) -> None:
        self._callback = callback

    def approve(self, action: AgentAction, description: str) -> bool:
        return bool(self._callback(action, description))


def get_approver(settings: Settings) -> Approver | None:
    """Map ``approval_mode`` to a synchronous approver.

    Returns ``None`` for ``manual`` mode: the caller (e.g. the API) is expected
    to handle the pause/resume flow itself rather than answering inline.
    """
    mode = settings.approval_mode.lower()
    if mode == "auto":
        return AutoApprover()
    if mode == "deny":
        return DenyAllApprover()
    return None  # manual
