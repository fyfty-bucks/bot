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
| 2 | [PLAN2](PLAN2.md) | LLM Integration | DONE |
| 3 | [PLAN3](PLAN3.md) | Telegram Bot + Agent Loop | — |
| 4 | [PLAN4](PLAN4.md) | Deploy to RPi | — |
| 5 | [PLAN5](PLAN5.md) | Survival I: CustDev | — |
| 6 | [PLAN6](PLAN6.md) | Survival II: Growth | — |
| 7 | [PLAN7](PLAN7.md) | Survival III: Consolidation | — |
| 8 | [PLAN8](PLAN8.md) | Autonomy | — |
| 9 | [PLAN9](PLAN9.md) | Agent State | GOAL |

---

## Current

**Phase:** 2 — LLM Integration — DONE
**Next:** Phase 3 — Telegram Bot + Agent Loop

---

## Tech Debt

### Phase 3 — Agent Loop

| ID | What | Why |
|----|------|-----|
| TD-1 | `db.atomic()` in agent loop | Multi-step tool loop needs transactional writes |
| TD-2 | `OpenRouterClient` accepts transport in ctor | Phase 3 modifies `LLM.call()`; clean DI replaces private attr injection in tests |

### Phase 4 — RPi Deploy

| ID | What | Why |
|----|------|-----|
| TD-3 | `BudgetLog.record()` race condition | Webhook = concurrent Telegram users writing budget |
| TD-4 | Budget tests: inject clock into `_compute_burn` | CI/cron on RPi runs at all hours; midnight edge case |

### Phase 5 — Real Money

| ID | What | Why |
|----|------|-----|
| TD-5 | `BudgetLog` float to Decimal | Payment precision requires exact arithmetic |
| TD-6 | `BudgetLog` overdraft guard | Negative balance ok now; must block with real payments |
| TD-7 | Budget SQL: Python loops to aggregates | ~3 alerts/day, hundreds of entries; revisit if scale demands |

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
