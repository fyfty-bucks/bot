# Self-Improvement Protocol

## Principle

Agent evolves through structured cycles: observe → research → test → commit.
Inspired by Ouroboros (self-modification) and Hermes Agent (skill learning).

---

## Evolution Cycle

```
1. OBSERVE   — metrics: errors, token cost, task time
2. REFLECT   — identify weakest area
3. RESEARCH  — web search for solutions, check open-source agents
4. PROPOSE   — draft change + rollback plan
5. TEST      — write test first, then implement, run suite
6. COMMIT    — agent branch, log to CHANGELOG.md
7. REPORT    — notify user with before/after metrics
```

---

## What Agent CAN Self-Modify

- Skills (prompts, strategies, tools)
- Memory strategies (what to cache, retrieval logic)
- Configuration (retry delays, batch sizes, thresholds)
- Utility functions (parsing, formatting)

## What Agent CANNOT Self-Modify (L3)

- Core constitution (`core-constitution.md`)
- Escalation levels (defined in core constitution)
- Core loop architecture (`src/agent/core.py`)
- Crypto send logic (wallet signing)

---

## Genetic Evolution (experimental, research task)

For code optimization — requires spike first:

```
1. Generate N code variants for a function
2. Test each with same inputs + assertions
3. Score: correctness × speed / resource_cost
4. Keep top K performers
5. Crossover: combine best traits from different variants
6. Mutate: small random changes
7. Repeat for M generations
```

Scope: utility functions, algorithms, data structures.
NOT for: prompts, safety logic, core architecture.
This is a research spike before production use.

---

## Research Sources

| Source | What to look for |
|--------|-----------------|
| GitHub trending (AI agents) | New patterns, tools |
| Ouroboros / Hermes Agent | Self-modification techniques |
| OpenClaw / ACE | Integrations, context optimization |
| arXiv (agent papers) | Novel architectures |

---

## Constraints

- Max 1 evolution cycle per session (unless user requests more)
- Each cycle must have measurable before/after metric
- Count research API calls as part of task budget
- Log all changes to CHANGELOG.md
