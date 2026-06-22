"""TaskPilot HTTP API.

    uvicorn taskpilot.api.main:app --reload

The agent runs in *manual* approval mode by default: ``POST /run`` may return a
``pending_approval`` block, which a human resolves with ``POST /approve``. With a
Redis backend this survives restarts; the in-memory backend keeps a singleton
agent so pending approvals persist within the process.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI
from pydantic import BaseModel, Field

from taskpilot.agent import TaskPilotAgent
from taskpilot.config import get_settings

app = FastAPI(title="TaskPilot", description="Agentic workflow automation bot", version="0.1.0")


@lru_cache
def get_agent() -> TaskPilotAgent:
    return TaskPilotAgent(get_settings())


class RunRequest(BaseModel):
    goal: str = Field(..., min_length=3, examples=["Summarise #general on Slack and email it to me@corp.com"])
    session_id: str | None = None


class ApproveRequest(BaseModel):
    approval_id: str
    approved: bool


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    agent = get_agent()
    return {
        "status": "ok",
        "planner": settings.llm_provider,
        "memory": settings.memory_backend,
        "approval_mode": settings.approval_mode,
        "connector_mode": settings.connector_mode,
        "tools": agent.registry.names(),
    }


@app.get("/tools")
def tools() -> dict:
    agent = get_agent()
    return {
        "tools": [
            {"name": t.name, "description": t.description, "requires_approval": t.requires_approval}
            for t in agent.registry.list()
        ]
    }


@app.post("/run")
def run(req: RunRequest) -> dict:
    return get_agent().run(req.goal, req.session_id).to_dict()


@app.post("/approve")
def approve(req: ApproveRequest) -> dict:
    return get_agent().resume(req.approval_id, req.approved).to_dict()
