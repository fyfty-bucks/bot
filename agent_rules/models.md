# Model Strategy (Agent Runtime)

## Principle

Two models: deterministic (fast) and non-deterministic (smart).
**Claude preferred. Spike to test providers before committing.**

---

## Two-Model Architecture

| Role | Use case | Candidate | Temperature |
|------|----------|-----------|-------------|
| Deterministic | Routing, classification, extraction, parsing | Claude Haiku | 0.0 |
| Non-deterministic | Reasoning, planning, code generation, research | Claude Sonnet | 0.2-0.5 |

### Deterministic (Fast)

- Strict system prompt, minimal context
- JSON output enforced
- No chain-of-thought
- Examples: task routing, data parsing, status checks, lint fixes

### Non-deterministic (Smart)

- Full context with memory and rules
- Chain-of-thought allowed
- Self-check required
- Examples: planning, debugging, self-improvement, code writing

---

## Provider Selection

Requires spike to test before production use:

| Provider | How to test | What to measure |
|----------|-------------|-----------------|
| OpenRouter | Python SDK or HTTP | Latency, cost, reliability |
| Direct Anthropic API | anthropic SDK | Latency, cost, uptime |
| BlockRun | x402 protocol | Crypto payment flow |

Spike goal: determine cheapest reliable path to Claude models.

---

## Fallback Chain

```
1. Try primary provider
2. If API error/timeout → retry once
3. If still fails → fallback to next provider
4. If all fail → queue task, notify user
```

---

## Budget Routing

When budget < 20% remaining:
- Route ALL tasks to deterministic model
- Disable self-improvement cycles
- Disable research/web search
- Notify user: "budget low, reduced to essential ops"

---

## Local Model (future, Phase 3+)

RPi 8GB can run small models (~3-7B params) via Ollama:
- Use for: offline health checks, simple classification
- NOT for: code generation, reasoning, research
- Spike required: test which models fit in 4GB (half of 8GB)

---

## Metrics Per Model

Track in agent.db:

| Field | Purpose |
|-------|---------|
| model | Which model |
| task_type | Classification, code, reasoning, etc. |
| tokens | In + out |
| cost | USD |
| latency_ms | Response time |
| success | Did task complete correctly |

Use metrics for: routing optimization, budget forecasting.
