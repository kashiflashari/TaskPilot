"""Persistent agent memory.

Stores per-session transcripts and pending approval requests. ``InMemoryStore``
is the offline/test default; ``RedisStore`` persists across restarts and
processes (used by the API in production).
"""

from __future__ import annotations

import json
from typing import Protocol

from taskpilot.config import Settings


class MemoryStore(Protocol):
    def load_session(self, session_id: str) -> dict | None: ...
    def save_session(self, session_id: str, data: dict) -> None: ...
    def save_pending(self, approval_id: str, data: dict) -> None: ...
    def load_pending(self, approval_id: str) -> dict | None: ...
    def delete_pending(self, approval_id: str) -> None: ...


class InMemoryStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}
        self._pending: dict[str, dict] = {}

    def load_session(self, session_id: str) -> dict | None:
        return self._sessions.get(session_id)

    def save_session(self, session_id: str, data: dict) -> None:
        self._sessions[session_id] = data

    def save_pending(self, approval_id: str, data: dict) -> None:
        self._pending[approval_id] = data

    def load_pending(self, approval_id: str) -> dict | None:
        return self._pending.get(approval_id)

    def delete_pending(self, approval_id: str) -> None:
        self._pending.pop(approval_id, None)


class RedisStore:
    """Redis-backed store. Keys are namespaced and JSON-encoded."""

    def __init__(self, settings: Settings) -> None:
        import redis

        self._r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        self._ttl = settings.memory_ttl_seconds

    def _skey(self, session_id: str) -> str:
        return f"taskpilot:session:{session_id}"

    def _pkey(self, approval_id: str) -> str:
        return f"taskpilot:pending:{approval_id}"

    def load_session(self, session_id: str) -> dict | None:
        raw = self._r.get(self._skey(session_id))
        return json.loads(raw) if raw else None

    def save_session(self, session_id: str, data: dict) -> None:
        self._r.set(self._skey(session_id), json.dumps(data), ex=self._ttl)

    def save_pending(self, approval_id: str, data: dict) -> None:
        self._r.set(self._pkey(approval_id), json.dumps(data), ex=self._ttl)

    def load_pending(self, approval_id: str) -> dict | None:
        raw = self._r.get(self._pkey(approval_id))
        return json.loads(raw) if raw else None

    def delete_pending(self, approval_id: str) -> None:
        self._r.delete(self._pkey(approval_id))


def get_memory(settings: Settings) -> MemoryStore:
    if settings.memory_backend.lower() == "redis":
        return RedisStore(settings)
    return InMemoryStore()
