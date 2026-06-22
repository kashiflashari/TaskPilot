# TaskPilot

**An agentic workflow automation bot** that executes multi-step workflows across Slack, Gmail, and Notion via MCP — with persistent memory and human-approval gates before any irreversible action.

Built around a **tool-calling agent loop** (OpenAI tool-calling / Agents-SDK-compatible schema), **MCP** tool integration, **Redis**-backed persistent memory, and an explicit **human-in-the-loop approval gate**.

> Runs **fully offline out of the box** — a deterministic rule-based planner drives the mock Slack/Gmail/Notion connectors, so you can watch the whole approval flow with no API keys. Plug in OpenAI + MCP servers + Redis for production.

---

## How it works

```
  goal ─▶ ┌─────────────┐   plan one step
          │   Planner   │   (OpenAI tool-calling / rule-based offline)
          └──────┬──────┘
                 ▼
          ┌─────────────┐   tool requires approval?
          │  Agent loop │ ──────────────┐ yes
          └──────┬──────┘                ▼
                 │ no            ⚠ Human-approval gate
                 ▼              (auto / manual pause+resume / deny)
          ┌─────────────┐                │ approved
          │ Execute tool│ ◀──────────────┘
          └──────┬──────┘
                 │ observation                    Slack · Gmail · Notion
                 ▼                                (mock connectors OR MCP servers)
          ┌─────────────┐
          │   Memory    │  persists transcript + pending approvals
          │ (Redis/mem) │  → survives restarts; resume by approval_id
          └──────┬──────┘
                 ▼
          loop until final answer / max steps
```

- **Agent loop** ([agent.py](src/taskpilot/agent.py)) — plans, executes, records to memory, enforces approval gates, and supports pause/resume.
- **Planners** ([planner/](src/taskpilot/planner/)) — `OpenAIPlanner` (tool-calling) for production; `RuleBasedPlanner` for offline/deterministic demos; `ScriptedPlanner` for tests.
- **Tools & connectors** ([connectors/](src/taskpilot/connectors/)) — Slack/Gmail/Notion capabilities; in-memory mocks for dev, or live **MCP servers** in production.
- **MCP provider** ([mcp_provider.py](src/taskpilot/mcp_provider.py)) — connects to MCP servers, exposes their tools, and flags side-effecting tools for approval.
- **Memory** ([memory.py](src/taskpilot/memory.py)) — in-memory or Redis store for transcripts and pending approvals.
- **Approval gates** ([approvals.py](src/taskpilot/approvals.py)) — `auto`, `manual` (pause + resume), or `deny`.

## Human-approval gate

Tools that send email, post to Slack, or create/append Notion pages are marked `requires_approval`. In **manual** mode the run pauses and returns a `pending_approval`; nothing irreversible happens until a human resumes it:

```bash
$ taskpilot run "Summarise #general on Slack and email it to boss@corp.com"

[!] Approval required: Run 'gmail_send_email' with arguments {'to': 'boss@corp.com', ...}
    Approve this action? [y/N] n

Status: denied
  [ok] slack_read_messages({"channel": "general"})
  [x]  gmail_send_email(...)   error: denied by approver
```

## Quickstart (offline, no keys)

```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -e ".[dev]"

python examples/quickstart.py        # pause → approve → complete

taskpilot run "Summarise #general on Slack and email it to me@corp.com"   # inline approval
taskpilot run "..." --auto           # approve everything (trusted automation)
taskpilot tools                      # list available tools
```

## Production setup

```bash
cp .env.example .env
pip install -e ".[openai,mcp,redis,api]"
```

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
MEMORY_BACKEND=redis
REDIS_URL=redis://localhost:6379/0
APPROVAL_MODE=manual
MCP_CONFIG_PATH=examples/mcp_config.example.json   # Slack / Gmail / Notion MCP servers
```

MCP servers are declared in a JSON config ([examples/mcp_config.example.json](examples/mcp_config.example.json)); their tools are auto-discovered and side-effecting ones are approval-gated.

## HTTP API

```bash
uvicorn taskpilot.api.main:app --reload
```

| Method | Path       | Description                                              |
| ------ | ---------- | -------------------------------------------------------- |
| GET    | `/health`  | Planner / memory / approval mode + tool list             |
| GET    | `/tools`   | Tools and which require approval                         |
| POST   | `/run`     | `{ "goal" }` → result, or a `pending_approval` block      |
| POST   | `/approve` | `{ "approval_id", "approved" }` → resumes the workflow    |

The pause/resume flow is stateful; with the Redis backend it survives restarts.

## Testing

```bash
pytest -q     # 20 tests, fully offline
```

Covers approval gating, manual pause/resume (including across a simulated restart), denial, the step cap, and the end-to-end Slack→email workflow.

## Project layout

```
src/taskpilot/
├── config.py            # pydantic-settings configuration
├── models.py            # Tool / AgentAction / WorkflowResult / ApprovalRequest
├── agent.py             # the tool-calling loop + approval gating + resume
├── registry.py          # tool registry + execution
├── approvals.py         # auto / manual / deny approvers
├── memory.py            # in-memory + Redis stores
├── mcp_provider.py      # MCP server integration
├── connectors/          # mock Slack / Gmail / Notion + tool definitions
├── planner/             # OpenAI / rule-based / scripted planners
├── api/                 # FastAPI app (/run, /approve)
└── cli.py               # `taskpilot` command
tests/                   # offline pytest suite
```

## Tech stack

| Layer          | Technology                       |
| -------------- | -------------------------------- |
| Agent runtime  | Tool-calling loop (OpenAI Agents SDK-compatible) |
| Tool transport | MCP servers                      |
| Integrations   | Slack / Gmail / Notion           |
| Memory         | Redis                            |
| API            | FastAPI                          |
| Packaging      | Docker                           |

## Design notes

- **Safety first** — irreversible actions are gated by default (`APPROVAL_MODE=manual`); the agent literally cannot send/post/create without explicit approval.
- **Durable pause/resume** — pending approvals and transcripts live in memory/Redis, so a workflow can be approved minutes later, by a different process.
- **Pluggable everything** — planner, connectors (mock vs MCP), memory, and approver are all swappable behind small interfaces; the offline path keeps the whole thing testable.

## Roadmap

- [x] Tool-calling agent loop with a step cap
- [x] Human-approval gate (auto / manual pause-resume / deny)
- [x] Slack / Gmail / Notion connectors (mock) + tool registry
- [x] MCP server integration
- [x] Redis + in-memory persistent memory
- [x] OpenAI + offline rule-based planners
- [x] FastAPI API, CLI, Docker Compose (with Redis), offline test suite
- [ ] Streaming step events over the API / websockets
- [ ] Scheduled & event-triggered workflows
- [ ] Per-tool approval policies and audit log export

## License

[MIT](./LICENSE)
