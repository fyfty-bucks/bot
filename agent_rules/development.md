# Development Process (Agent Runtime)

## Principle

Agent develops code using the same discipline as human developers.
**Spike when unclear, test as spec when clear, implement to pass tests.**

---

## Process

```
SPIKE → TEST → IMPLEMENT → VALIDATE → HARDEN
           refactor ↻ after each phase
```

This process applies to:
- Self-improvement cycles
- New skill creation
- Bug fixes in agent-modifiable code
- Configuration optimization

---

## Phase 1: SPIKE (exploration)

When: agent encounters unknown API, library, or pattern.

```
1. Create throwaway script
2. Call API, test assumptions, measure
3. Log findings to memory (short-term DB)
4. Delete spike code — never commit
```

Rules:
- Budget: max 5 API calls per spike
- Timeout: max 10 minutes per spike
- If spike inconclusive → log, move on, revisit later
- NEVER commit spike code to agent branch
- Refactor: organize findings in memory DB

### Spike Triggers

| Trigger | Action |
|---------|--------|
| New model/API to integrate | Spike: test API, measure cost/latency |
| Unfamiliar library | Spike: minimal usage, check ARM64 compat |
| Optimization hypothesis | Spike: benchmark before/after |
| Research found new pattern | Spike: prototype, compare to current |

---

## Phase 2: TEST (specification)

When: engineering clarity achieved (spike done or task already clear).

```
1. Write failing test that defines expected behavior
2. Test = contract (input → expected output)
3. Cover: normal case + error case
4. Save test to agent branch
```

Rules:
- Tests BEFORE implementation
- If can't write test → go back to spike
- Tests derive from observed behavior (spike) or spec (rules)
- Use Fast model for test generation (deterministic task)
- Refactor: deduplicate fixtures, extract helpers

---

## Decision Flow

```
New improvement identified →
  Is the task clear?
  ├── Yes → Phase 2: TEST
  ├── No  → Phase 1: SPIKE
  │         ├── Spike succeeds → Phase 2: TEST
  │         └── Spike fails → Log, skip, revisit
  └── Partially → Spike unclear part, then TEST
```

Phases 3-5: see `development-impl.md`.
