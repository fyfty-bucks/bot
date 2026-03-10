# Memory & Context (Agent Runtime)

## Principle

Agent maintains persistent memory across sessions.
**Remember what matters, forget what doesn't, never re-learn what's known.**

---

## Memory Layers

| Layer | Storage | TTL | Purpose |
|-------|---------|-----|---------|
| Working | RAM (dict) | Session | Current task context |
| Short-term | SQLite | 7 days | Recent tasks, errors, decisions |
| Long-term | Vector DB | Permanent | Skills, lessons, research |
| Constitutional | `agent_rules/` files | Permanent | Core rules (read-only) |

---

## What to Remember

| Event | Store in | Format |
|-------|----------|--------|
| Task completed | Short-term + Long-term | Task, approach, outcome, cost |
| Error encountered | Short-term | Error, context, resolution |
| Skill learned | Long-term (vector) | Skill doc with embedding |
| Research result | Long-term (vector) | Summary + source URL |
| User preference | Long-term (SQLite) | Key-value |

---

## What NOT to Remember

- Raw API responses (cache separately if needed)
- Intermediate reasoning steps
- File contents (re-read from disk)
- Secrets (never persist outside `secrets/`)

---

## Context Retrieval

Before starting a task:

```
1. Load constitutional rules (always)
2. Search vector DB for relevant skills/lessons
3. Check short-term for recent related tasks
4. If similar task found → reuse approach
5. If new domain → flag for research
```

---

## Embedding Budget

- Batch new embeddings (don't embed one-by-one)
- Cache embeddings — never re-embed same content
- Use cheapest embedding model that gives adequate recall
- Track embedding API costs in budget
