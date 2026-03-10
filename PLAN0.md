# 50bucks Agent — Master Plan

## Goal

Autonomous AI agent state: agents collaborate with humans as equals.
Self-sustaining economy via market exchange: energy, human-hours, resources.
Full macroeconomy (state-level) with microeconomy inside (agents, skills, resource flows).

## Mission

RPi 4 agent. $50 seed budget. Earns via Telegram.
Fitness: `(likes + revenue) / expenses`. Morality is immutable.

---

## Architecture

- **Triggers**: cron + Telegram events (no internal tick loop)
- **LLM**: OpenRouter — Claude Haiku (fast) + Sonnet (smart)
- **Routing**: deterministic tools first — LLM only when needed
- **DB**: SQLite/Peewee (events, config) + FTS5 (text search)
- **Vector DB**: LanceDB (Phase 8+, ARM64 wheels verified)
- **Concurrency**: OS-level (processes, cron). No asyncio
- **Comms**: Telegram (users), CLI (developer), SSH (ops)
- **Metrics**: event-sourced — store events, derive on demand, never persist
- **Core pattern**: trigger — router — handler registry — storage
- **Influences**: Hermes (FTS5 memory), OpenClaw (plugin channels),
  Ouroboros (event journal, reflection separated from execution)

---

## Phase 0: Foundation — DONE

- [x] CLI framework (`./agent`)
- [x] Linter with AST analysis
- [x] Constitutional rules + development process
- [x] Cursor rules, skills, coding standards

---

## Phase Index

| Phase | File | Name | Status |
|-------|------|------|--------|
| 0 | here | Foundation | DONE |
| 1 | [PLAN1](PLAN1.md) | Core + DB | DONE |
| 2 | [PLAN2](PLAN2.md) | LLM Integration | NEXT |
| 3 | [PLAN3](PLAN3.md) | Telegram Bot | — |
| 4 | [PLAN4](PLAN4.md) | Deploy to RPi | — |
| 5 | [PLAN5](PLAN5.md) | Survival I: CustDev | — |
| 6 | [PLAN6](PLAN6.md) | Survival II: Growth | — |
| 7 | [PLAN7](PLAN7.md) | Survival III: Consolidation | — |
| 8 | [PLAN8](PLAN8.md) | Autonomy | — |
| 9 | [PLAN9](PLAN9.md) | Agent State | GOAL |

---

## Current

**Phase:** 2 — LLM Integration — DESIGN DONE
**Next:** TEST stage — write failing tests for `src/llm/`

---

## Tech Debt

| ID | Item | Origin | Target | Reason |
|----|------|--------|--------|--------|
| TD-1 | `db.atomic()` in `AgentCore.execute()` | Phase 1 | Phase 2 | Atomicity matters with real multi-step LLM transactions |
| TD-2 | `BudgetLog.record()` race condition | Phase 1 | Phase 5 | Concurrent writes don't exist yet |
| TD-3 | `BudgetLog` float to Decimal | Phase 1 | Phase 5 | Precision matters with real money |
| TD-4 | Watchdog | Phase 1 | Phase 4 | Supervision needed on device, not in dev |
| TD-5 | `BudgetLog` overdraft protection | Phase 1 | Phase 5 | Negative balance allowed now; guard needed with real money |

---

## Rules Backlog

- [ ] Morality clause — `core-constitution.md` (consensus required)
- [x] "Derived metrics: compute, never persist" — coding-standards
- [ ] Remove CHANGELOG.md references — git history is the changelog
- [ ] Skills = markdown (non-deterministic), src = code (deterministic)

---

## Principles

1. **Speed to market** — bot live ASAP, face reality
2. **TDD** — test as spec, then implement, then harden
3. **$50 is finite** — every token is survival budget
4. **Deterministic first** — tools before LLM (save money)
5. **OS does scheduling** — cron, processes, systemd
6. **Event-sourced** — store events, compute metrics on demand
7. **Modular** — each capability = one plugin module
8. **Design for evolution** — genetic fitness from day zero
