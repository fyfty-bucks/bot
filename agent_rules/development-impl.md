# Development: Implement → Validate → Harden

Continuation of `development.md`. Phases 3-5.

---

## Phase 3: IMPLEMENT

```
1. Write minimal code to pass tests
2. Run tests — all green
3. Refactor: extract, rename, split if >200 lines
```

Rules:
- Use Smart model for implementation (reasoning task)
- Minimal code — pass tests, nothing more
- If tests fail after 3 attempts → abort, log, notify
- Refactor before moving to next phase

---

## Phase 4: VALIDATE

```
1. Run lint
2. Run full test suite (no regressions)
3. Check file limits (≤200 lines)
4. Fix any violations
```

Rules:
- Use Fast model for lint fixes (deterministic)
- If new failures in other modules → fix or revert
- Refactor: fix lint violations, simplify

---

## Phase 5: HARDEN

```
1. Add edge case tests (timeout, bad input, network down)
2. Add error handling to implementation
3. Re-run full suite
4. Commit to agent branch
5. Log: what changed, metrics before/after
```

Rules:
- Use Smart model for edge case reasoning
- Error paths must be tested, not assumed
- One commit per logical change
- Refactor: extract error handling patterns

---

## Integration with Self-Improvement

```
OBSERVE → REFLECT → RESEARCH     = identifies what to improve
SPIKE                             = explores how to improve
TEST                              = defines success criteria
IMPLEMENT                         = makes the change
VALIDATE                          = ensures quality
HARDEN                            = covers edge cases
COMMIT → REPORT                   = ships and logs
       refactor ↻ after each phase
```

---

## Anti-Patterns

| Bad | Good |
|-----|------|
| Implement without tests | Tests define contract first |
| Spike forever | Spike has budget (5 calls, 10 min) |
| Commit spike code | Spike is throwaway |
| Skip spike when unclear | Spike turns ambiguity into clarity |
| Test from implementation | Test from spec/behavior |
| Retry failing impl forever | 3 attempts max, then abort |
| Skip validate | Lint + full suite every time |
| Skip harden | Edge cases prevent prod failures |
| No refactor between phases | Refactor keeps code clean |
