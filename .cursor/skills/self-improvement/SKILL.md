# Skill: Implement Self-Improvement Features

Guide for Opus 4.6 when coding agent's self-improvement capabilities.

---

## When to Use

- Implementing evolution cycle logic
- Writing genetic algorithm components
- Building metrics collection
- Coding research/web-search integration

---

## Reference

Agent spec: `agent_rules/self-improvement.md`
Process: `agent_rules/development.md`, `agent_rules/development-impl.md`

---

## Modules

| Module | Purpose | Location |
|--------|---------|----------|
| Metrics collector | Track errors, tokens, cost, time per task | `src/agent/metrics.py` |
| Evolution cycle | OBSERVE → REFLECT → RESEARCH → SPIKE → TEST → IMPL | `src/agent/evolve.py` |
| Genetic optimizer | Code variant evolution, fitness scoring | `src/agent/genetic.py` |

---

## Metrics to Track (in agent.db)

| Metric | Use |
|--------|-----|
| task_type | Route optimization |
| tokens_used | Cost analysis |
| errors | Weakness detection |
| duration_s | Performance baseline |
| success | Success rate per module |

---

## Genetic Optimizer Scope (research task)

Apply to: code (utility functions, algorithms, data structures).
NOT for: prompts, safety rules, core architecture, API integration.

Approach: generate N code variants → test with same assertions → score (correctness × speed / resource_cost) → keep top K → crossover + mutate → repeat.
Requires spike before production use.

---

## Testing

- Unit test each phase independently
- Mock LLM calls in tests
- Test rollback path (revert on failure)
- Integration test: full cycle with mock metrics
