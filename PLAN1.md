# Phase 1: Core + DB

**Status:** DONE

---

## Scope

Agent core loop, database layer, event sourcing, configuration system.

## Dependencies

Phase 0 (Foundation) — DONE

## Deliverables

**Core:**
- [x] Event model with FTS5 search index
- [x] Task model with state machine lifecycle
- [x] Budget tracking model
- [x] Config store (key-value, 3-tier: env > db > defaults)
- [x] Agent core loop: receive — route — execute — store
- [x] Handler registry with plugin discovery

**Harden (audit):**
- [x] Linter: full test coverage, single AST parse, DRY, secret patterns
- [x] `Config.load()` logs warning on coercion fallback
- [x] `AgentCore.execute()` uses `registry.route()` API
- [x] `_flatten_values()` depth limit (prevent stack overflow)
- [x] `get_db()` safe connect + close contract
- [x] `pyproject.toml` single dependency source
- [x] DRY rule added to coding standards
- [x] Rules trimmed for context efficiency

**Refactor:**
- [x] Split `_lint_core.py`: secret scanner — `_lint_secrets.py`
- [x] Linter config: limits in `pyproject.toml`, loaded by `_lint_config.py`
- [x] `info` command: actual DB stats (events, tasks, budget via `--db`)

## Gate

All deliverables complete.
Tech debt registered in [PLAN0](PLAN0.md): TD-1, TD-2, TD-3, TD-4.
