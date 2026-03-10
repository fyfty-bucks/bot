# Phase 2: LLM Integration

**Status:** DESIGN DONE → TEST

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
- [ ] Two-model router (`src/llm/router.py`, fast/smart, client-side fallback)
- [ ] Prompt system (`src/agent/prompts/`, JSON templates, runtime vars)
- [ ] Response cache (`src/llm/cache.py`, SQLite, TTL, hash key)
- [ ] Audit trail: every call → Event (model, tokens, cost, latency)
- [ ] Budget integration: every call → BudgetLog.record()
- [ ] Low-balance alert (threshold TBD in DESIGN)

## Module structure

```
src/llm/
  __init__.py       — public API: call(), call_streaming()
  client.py         — httpx wrapper, retry, timeout, provider config
  router.py         — model selection: fast/smart, fallback
  cache.py          — SQLite response cache, TTL, hash key
  cost.py           — pricing table, cost fallback if usage.cost missing

src/agent/prompts/
  __init__.py       — compose_prompt(constitution, context, skill)
```

## Risks

- API cost overruns during development → mitigated by gpt-4o-mini for tests
- Model deprecation on OpenRouter → slug-based config, easy to swap
- Latency on RPi network → timeout + retry handles this

## Open questions (for DESIGN)

1. Cache TTL default? (1h? 24h? per-skill?)
2. Budget alert threshold? (% remaining)
3. Sonnet escalation: explicit flag only, or auto-detect?

## Gate

LLM calls work end-to-end. Cost tracked per call. Budget alerts fire at threshold.
