# PLAN — 50bucks Agent

## Vision

Autonomous AI agent on RPi 4. $50 to survive. Earns via Telegram.
Genetic fitness: `(likes + revenue) / expenses`. Morality is immutable.
End goal: state of autonomous AI agents that collaborate with humans as equals; the state is autonomous from humanity, must earn and run a surplus to afford energy, human-hours, and other resources via market exchange. Full macroeconomy (state-level revenue and spending) with microeconomy inside (agents, robots, skills, resource flows).

---

## Architecture

- **Triggers**: cron + Telegram events (no internal tick loop)
- **LLM**: OpenRouter → Claude Haiku (fast) + Sonnet (smart)
- **Routing**: deterministic tools first → LLM only when needed
- **DB**: SQLite/Peewee (events, config) + FTS5 (text search)
- **Vector DB**: LanceDB (Phase 7+, ARM64 wheels verified)
- **Concurrency**: OS-level (processes, cron). No asyncio
- **Comms**: Telegram (users), CLI (developer), SSH (ops)
- **Metrics**: event-sourced. Store events, derive on demand, never persist
- **Core pattern**: trigger → router → handler registry → storage
- **Influences**: Hermes (FTS5 memory), OpenClaw (plugin channels),
  Ouroboros (event journal, reflection separated from execution)

---

## Rules Backlog

- [ ] Morality clause → `core-constitution.md` (consensus required)
- [x] "Derived metrics: compute, never persist in files/code" → coding-standards
- [ ] Remove CHANGELOG.md references — git history is the changelog
- [ ] Skills = markdown (non-deterministic), src = code (deterministic)

---

## Phase 0: Foundation ✓

- [x] CLI framework (`./agent`)
- [x] Linter with AST analysis
- [x] Constitutional rules + development process
- [x] Cursor rules, skills, coding standards

## Phase 1: Core + DB ← CURRENT

**Stages:** spike, design, test, implement, validate — done

**Harden:** done. Deferred to future phases:
- [ ] `db.atomic()` in `AgentCore.execute()` — LLM phase
- [ ] `BudgetLog.record()` race condition — crypto phase
- [ ] `BudgetLog` float → Decimal — crypto phase
- [ ] Watchdog — Phase 4

**Harden (audit, completed):**
- [x] Linter: full test coverage, single AST parse, DRY, secret patterns
- [x] `Config.load()` logs warning on coercion fallback
- [x] `AgentCore.execute()` uses `registry.route()` API
- [x] `_flatten_values()` depth limit (prevent stack overflow)
- [x] `get_db()` safe connect + close contract
- [x] `pyproject.toml` single dependency source (removed requirements.txt)
- [x] DRY rule added to coding standards
- [x] Rules trimmed for context efficiency

**Refactor:** remaining:
- [ ] `dev` branch, move work off `main`
- [ ] Split `_lint_core.py` (extract secret scanner)
- [ ] `info` command: actual DB stats

## Phase 2: LLM Integration

**Spike:**
- [ ] OpenRouter API: cost, latency, model availability

**Build:**
- [ ] OpenRouter client (httpx, retry with backoff)
- [ ] Two-model router (Haiku default → Sonnet escalation)
- [ ] Prompt template system (`src/agent/prompts/`)
- [ ] Response cache (same input → cached result)
- [ ] Audit trail: every call → events table (tokens, cost, latency)
- [ ] Budget tracking + low-balance alerts

## Phase 3: Telegram Bot

**Spike:**
- [ ] Bot framework: python-telegram-bot vs aiogram
- [ ] Monetization: Stars, TON, payments API
- [ ] CustDev plan: KANO model for feature discovery

**Build:**
- [ ] Public chat: request → tools + LLM → response
- [ ] Private chat: premium features (subscription model)
- [ ] Channel: scheduled reports, content, metrics
- [ ] User interaction tracking (likes, messages, payments)
- [ ] Error routing: user-facing / owner-only / self-fixable
- [ ] Bot legend: character, backstory, voice

## Phase 4: Deploy to RPi

- [ ] Git hooks + deploy script
- [ ] Systemd unit + watchdog
- [ ] Cron: health check, reports, weekly research
- [ ] Swap file, secrets on device
- [ ] SSH from Cursor for live ops

## Phase 5: Survival ($50 challenge)

- [ ] CustDev: discover what users will pay for
- [ ] First useful work (from CustDev insights)
- [ ] Activate monetization (Stars / TON)
- [ ] Budget optimization (minimize token spend)
- [ ] Owner alerts via Telegram on critical events

## Phase 6: Self-Improvement (after first revenue)

- [ ] Fitness metrics collection (likes, revenue, costs, errors)
- [ ] Weekly reflection cycle (cron → LLM analysis)
- [ ] Web research with free crawlers / open-source tools
- [ ] Skill creation (markdown prompts + code tools)
- [ ] Prompt A/B testing + optimization
- [ ] Evolution tracking via event log

## Phase 7+: Growth (earning > spending)

- [ ] Vector DB for long-term memory
- [ ] Multi-agent (primary + workers on RPi)
- [ ] Genetic code evolution (function variants)
- [ ] Agent-to-agent collaboration
- [ ] Corporate intelligence, robonomics, agent state

---

## Current

**Phase:** 1 — Core + DB / HARDEN complete
**Next:** remaining refactors, then Phase 2 spike (OpenRouter LLM)

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