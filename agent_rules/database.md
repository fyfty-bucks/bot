# Database Architecture (Agent Runtime)

## Principle

Embedded databases only. No external servers.

---

## Databases

| DB | Engine | Purpose |
|----|--------|---------|
| `agent.db` | SQLite via ORM | Config, budget log, task log, skill registry |
| `memory.vec` | TBD (spike: ARM64 compat test) | Embeddings, semantic search, long-term memory |

---

## ORM Contract

- ALL relational operations through Peewee ORM
- Bulk writes: use built-in batching
- Transactions: `db.atomic()` for writes
- SQLite: `journal_mode=WAL` for concurrent reads

---

## Vector DB Usage

| Use case | What to store |
|----------|--------------|
| Task memory | Past tasks, outcomes, lessons learned |
| Skill lookup | Skill descriptions → semantic match |
| Code context | Code summaries for self-improvement |
| Research cache | Web search results, API docs |

### Embedding Strategy

- Remote embedding API (RPi can't run models locally)
- Cache embeddings aggressively — each call costs money
- Batch embedding requests

---

## RPi Constraints

- Keep vector index in RAM, data on disk
- Monitor disk usage — SD card limited
- Prefer USB SSD for DB files if available

---

## NEVER

- Raw `sqlite3` in code — use ORM
- Store secrets in DB
- Run embedding models locally on RPi
- Delete DB files without user confirmation (L2)
