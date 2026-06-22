# TaskPilot

**An agentic workflow automation bot** that executes multi-step workflows across Slack, Gmail, and Notion via MCP — with persistent memory and human-approval gates before any irreversible action.

> **Status:** 🚧 In active development. Architecture and roadmap below; implementation in progress.

---

## Overview

TaskPilot is a tool-calling agent that gets real work done across your everyday tools. It plans and executes multi-step workflows — read a Slack thread, draft and send an email, update a Notion page — by calling tools exposed through MCP servers. It remembers context across runs and, critically, pauses for explicit human approval before doing anything irreversible (sending an email, deleting a record, posting publicly).

## How it works

```
   request ──▶ ┌─────────────────┐
               │  Tool-calling   │  plans the workflow, picks tools
               │     agent       │
               └────────┬────────┘
                        │ calls tools via MCP
            ┌───────────┼───────────┐
            ▼           ▼           ▼
        ┌───────┐   ┌───────┐   ┌────────┐
        │ Slack │   │ Gmail │   │ Notion │   (MCP servers)
        └───────┘   └───────┘   └────────┘
                        │
                        ▼
              ⚠ Human-approval gate   ← before any irreversible action
                        │ approved
                        ▼
                  action executed
                        │
                        ▼
              Redis memory (persists context across steps & runs)
```

- **Tool-calling agent** — plans and executes multi-step workflows across connected services.
- **MCP integration** — Slack, Gmail, and Notion exposed as tools via MCP servers.
- **Persistent memory** — Redis-backed memory carries context across steps and sessions.
- **Human-approval gates** — irreversible actions pause for explicit confirmation before executing.

## Tech stack

| Layer          | Technology                       |
| -------------- | -------------------------------- |
| Agent runtime  | OpenAI Agents SDK                |
| Tool transport | MCP servers                      |
| Integrations   | Slack / Gmail / Notion APIs      |
| Memory         | Redis                            |
| Packaging      | Docker                           |

## Key features

- Multi-step workflow execution across Slack, Gmail, and Notion.
- Tool calling through standardized MCP servers.
- Persistent, Redis-backed memory across steps and runs.
- Human-in-the-loop approval gates before irreversible actions.

## Roadmap

- [ ] Tool-calling agent core (OpenAI Agents SDK)
- [ ] MCP servers for Slack, Gmail, Notion
- [ ] Redis-backed persistent memory
- [ ] Human-approval gate for irreversible actions
- [ ] Example end-to-end workflows
- [ ] Dockerfile + deployment guide

## Getting started

> Setup instructions will be added as the implementation lands.

```bash
# Coming soon
git clone https://github.com/kashiflashari/TaskPilot.git
cd TaskPilot
```

## License

[MIT](./LICENSE)
