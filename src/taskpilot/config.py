"""TaskPilot configuration, loaded from environment / ``.env``.

Defaults are safe and offline: a deterministic stub planner, in-memory store,
mock connectors, and *manual* approval for irreversible actions.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # --- Planner: stub | openai -----------------------------------------
    llm_provider: str = "stub"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"
    temperature: float = 0.1
    max_steps: int = 8  # safety cap on the agent loop

    # --- Memory: memory | redis -----------------------------------------
    memory_backend: str = "memory"
    redis_url: str = "redis://localhost:6379/0"
    memory_ttl_seconds: int = 60 * 60 * 24 * 7

    # --- Approvals: auto | manual | deny --------------------------------
    # manual  → irreversible actions pause and require explicit approval
    # auto    → approve everything (use only in trusted automation)
    # deny    → reject every approval-gated action
    approval_mode: str = "manual"

    # --- Connectors: mock | real ----------------------------------------
    connector_mode: str = "mock"
    slack_bot_token: str | None = None
    gmail_credentials_path: str | None = None
    notion_api_key: str | None = None

    # --- MCP -------------------------------------------------------------
    mcp_config_path: str | None = None  # JSON describing MCP servers to connect


@lru_cache
def get_settings() -> Settings:
    return Settings()
