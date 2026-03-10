# Multi-Agent System

## Principle

Primary agent can fork sub-agents on the same hardware.
**One primary, N workers. Primary orchestrates, workers execute.**

---

## Architecture

```
Primary Agent (PID 1)
├── Worker: task-executor      # Runs deterministic tasks
├── Worker: researcher         # Web search, synthesis
├── Worker: monitor            # Health, budget, cron
└── (future) External agents   # Other machines, humans
```

All share: same filesystem, same DB, same git repo.
Each has: own process, own context window, own model tier.

---

## Fork Rules

Primary agent MAY fork a worker when:
- Task is independent (no shared state mutation)
- Task can run with Fast model
- Total RAM usage < 6GB after fork

Primary agent MUST NOT fork when:
- RAM > 6GB used
- Task modifies shared files (use primary)
- More than 3 workers already running

---

## Worker Lifecycle

```
1. Primary creates worker config (task, model, timeout)
2. Worker starts as subprocess
3. Worker reads task, executes, writes result to DB
4. Worker exits
5. Primary reads result from DB
```

No long-lived workers (RPi resource constraint).
Exception: monitor worker (lightweight, always-on).

---

## Communication

### Between agents on same machine

| Method | Use case |
|--------|----------|
| SQLite (agent.db) | Task queue, results, shared state |
| Filesystem | Large data, files |
| Unix signals | Kill, pause |

No HTTP/gRPC between local agents — overhead not justified on RPi.

### With humans (current)

| Channel | Direction | Format |
|---------|-----------|--------|
| SSH terminal | Bidirectional | CLI structured output |
| Git commits | Agent → human | Code + commit message |
| CHANGELOG.md | Agent → human | Append-only log |

### With humans (future)

| Channel | Direction | Notes |
|---------|-----------|-------|
| Telegram | Bidirectional | Notifications, commands |
| Email | Agent → human | Reports, alerts |
| Web UI | Bidirectional | Dashboard, config |

### With other agents (future)

| Method | Use case |
|--------|----------|
| HTTP API | Agent-to-agent on different machines |
| Shared git repo | Async collaboration via branches |
| Message queue | If scaling beyond RPi |

---

## Communication Protocol (agent-to-agent, future)

```json
{
  "from": "agent-id",
  "to": "agent-id | human-id | broadcast",
  "type": "task | result | status | error",
  "payload": {},
  "timestamp": "ISO8601",
  "requires_response": true
}
```

---

## Isolation

| Resource | Shared | Isolated |
|----------|--------|----------|
| Filesystem | Yes (same repo) | Write to own dirs only |
| Database | Yes (agent.db) | Own tables/namespaces |
| API keys | Yes (secrets/) | Read-only |
| Git | Yes (agent branch) | Primary commits only |
| Network | Yes | Workers: no outbound unless task requires |

---

## Scaling Path

```
Phase 1: Single agent, single model          ← NOW
Phase 2: Single agent, multi-model routing
Phase 3: Primary + workers on same RPi
Phase 4: Multi-machine (RPi cluster or cloud workers)
Phase 5: Agent-to-agent collaboration
```
