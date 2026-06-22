import pytest

from taskpilot.config import Settings
from taskpilot.connectors import build_workspace
from taskpilot.memory import InMemoryStore


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        llm_provider="stub",
        memory_backend="memory",
        approval_mode="manual",
        connector_mode="mock",
        max_steps=8,
    )


@pytest.fixture
def workspace(settings):
    return build_workspace(settings)


@pytest.fixture
def store():
    return InMemoryStore()
