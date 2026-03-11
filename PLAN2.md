# Phase 2: LLM Integration

**Status:** TEST DONE → IMPLEMENT

---

## Scope

Connect agent to LLM via OpenRouter. Two-model routing, cost tracking, caching.

## Dependencies

Phase 1 (Core + DB) — DONE

## Spike — DONE

- [x] OpenRouter API: cost per model, latency, availability
- [x] Rate limits, error codes, retry semantics
- [x] Token counting: API-reported (no tiktoken needed)

### Spike findings

**API contract:** `POST /chat/completions` (OpenAI-compatible). `usage.cost` returned
in every response — exact cost, no manual calculation. Streaming: usage in final SSE chunk.

**Models (verified pricing from /models):**

| Model | Input $/M | Output $/M | Context | Role |
|---|---|---|---|---|
| `openai/gpt-4o-mini` | $0.15 | $0.60 | 128K | Dev/test |
| `anthropic/claude-haiku-4.5` | $1.00 | $5.00 | 200K | Prod fast |
| `anthropic/claude-sonnet-4.5` | $3.00 | $15.00 | 1M | Prod smart |

**Error contract:** `{"error": {"message": str, "code": int}}` — uniform across all errors.

| Code | Retry |
|---|---|
| 400, 401, 402, 403 | No (fail fast; 402 → alert owner) |
| 408 | Once, longer timeout |
| 429, 502, 503 | Exponential backoff |

**Caching (verified live):**
- Server-side: works only for OpenAI with `provider.only` + `user` (45% savings).
  Anthropic prompt caching broken on OpenRouter (known bugs).
- Client-side: SHA256 hash of `(model, messages, temperature)` → SQLite. Primary strategy.
- Budget at 50 calls/day on Haiku: $0.08/day without cache → 625 days.
  With client cache 40% hit rate → 1042 days.

**Model fallback:** `models[]` array does NOT work (400 on first invalid).
Client-side routing required.

**System prompts (verified):** JSON, Markdown, plain text — all work equally.
JSON is 17% more tokens but convenient for programmatic composition.
`system` + `developer` roles combine. Leak protection works with explicit rule.

**Decisions:**

| Choice | Reason |
|---|---|
| httpx (not SDK) | Already in deps, full control, easy mock |
| No tiktoken | API reports native token counts |
| Client-side SQLite cache | 100% hit savings, deterministic |
| `provider.only` + `user` | Free OpenAI server-cache bonus |
| Client-side model routing | `models[]` array broken |
| JSON system prompts | Programmatic composition via dict |
| gpt-4o-mini for tests | $0.15/$0.60, cheapest |

## Deliverables

- [ ] OpenRouter client (`src/llm/client.py`, httpx, retry with backoff)
- [ ] Two-model router (`src/llm/__init__.py`, LLM._resolve_model, tier-based)
- [ ] Response cache (`src/llm/cache.py`, SQLite, TTL, SHA256 key)
- [ ] Audit trail: every call → Event (model, tokens, cost, latency)
- [ ] Budget integration: every call → BudgetLog.record()
- [ ] Budget guard: check_budget() + check_alerts() + BudgetExhausted
- [ ] Prompt system (`src/agent/prompts/`) — deferred to Phase 3

## Module structure

```
src/llm/
  __init__.py       — public API: LLM.call(), ModelTier, LLMResult
  client.py         — httpx wrapper, retry, timeout, RawResponse
  errors.py         — ClientError, ServerError
  cache.py          — SQLite response cache, TTL, SHA256 key
  budget.py         — check_budget(), record_cost(), check_alerts()

src/agent/prompts/  — deferred to Phase 3
```

## Risks

- API cost overruns during development → mitigated by gpt-4o-mini for tests
- Model deprecation on OpenRouter → slug-based config, easy to swap
- Latency on RPi network → timeout + retry handles this

## Design decisions (resolved)

1. Cache TTL: 7 days default (`config.cache_ttl = 604800`), per-call override via `cache_ttl` param
2. Budget alert: days-to-depletion model (ok >7d, warning 3–7d, critical 1–3d, danger <1d, depleted ≤0)
3. Sonnet escalation: explicit `tier=ModelTier.SMART` only; auto-downgrade to FAST on critical/danger

## Tech Debt (HARDEN)

- [ ] `LLM.call()` propagating `ClientError`/`ServerError` — no test
- [ ] `httpx.TimeoutException` (network failure) — no test
- [ ] Malformed API response (missing `choices`/`usage`) — no test
- [ ] Alert dedup cross-day behavior (next day re-emits) — no test
- [ ] `record_cost` with zero cost — no test
- [ ] Budget burn rate: specify behavior when zero LLM spend in window

## Gate

LLM calls work end-to-end. Cost tracked per call. Budget alerts fire at threshold.
