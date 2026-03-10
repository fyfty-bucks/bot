# Phase 2: LLM Integration

**Status:** NOT STARTED

---

## Scope

Connect agent to LLM via OpenRouter. Two-model routing, cost tracking, caching.

## Dependencies

Phase 1 (Core + DB) — DONE

## Spike

- [ ] OpenRouter API: cost per model, latency, availability
- [ ] Rate limits, error codes, retry semantics
- [ ] Token counting: tiktoken or API-reported

## Deliverables

- [ ] OpenRouter client (`src/llm/`, httpx, retry with backoff)
- [ ] Two-model router (Haiku default — Sonnet escalation)
- [ ] Prompt template system (`src/agent/prompts/`)
- [ ] Response cache (same input — cached result, TTL)
- [ ] Audit trail: every call — events table (model, tokens, cost, latency)
- [ ] Budget tracking + low-balance alerts

## Risks

- API cost overruns during development
- Model deprecation on OpenRouter
- Latency on RPi network

## Gate

LLM calls work end-to-end. Cost tracked per call. Budget alerts fire at threshold.
