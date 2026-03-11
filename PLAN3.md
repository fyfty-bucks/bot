# Phase 3: Telegram Bot + Agent Loop

**Status:** NOT STARTED (blocked by Phase 2 HARDEN)

---

## Scope

Agent loop (multi-step LLM + tool calling) + Telegram bot.
The loop is the execution engine: trigger → [LLM ↔ tools]* → response.
Telegram is the first trigger and delivery channel.

## Dependencies

Phase 2 (LLM) — HARDEN must be done first

## Architecture — cascade cost model

```
Trigger (Telegram / CLI)
  → Router: try deterministic handler first (zero cost)
    → If handled: return
    → Else: Agent Loop
      → LLM.call(messages + tool_defs)
      → If tool_calls: execute tools, feed results, loop
      → If text: return response
      → Guards: max_steps, budget check per step
```

**Tier 0 — Deterministic:** existing `HandlerRegistry`. Zero LLM cost.
Example: `/balance`, `/status`, `/help`.

**Tier 1 — Single-shot:** one `LLM.call()`, no tools.
Used when answer needs LLM but no external data.

**Tier 2 — Tool loop:** LLM + tool calls, capped at `max_steps` (config, default 5).
LLM decides whether to call tools. Budget guard checks every iteration.

Tier selection is automatic — LLM decides. No manual routing.

## Spike

- [ ] Tool calling via OpenRouter with Haiku (exact payload format)
- [ ] Token overhead of N tool definitions
- [ ] Multi-step loop cost (2-3 steps with tools)
- [ ] `finish_reason` values: tool_calls vs stop
- [ ] Parallel tool calls (does Haiku batch multiple tool_calls?)
- [ ] Bot framework: python-telegram-bot vs aiogram
- [ ] Monetization APIs: Stars, TON, payments
- [ ] Webhook vs polling on RPi constraints

## Changes to existing code

**`src/llm/client.py`** — `RawResponse` + `_parse_response`:
- Add `tool_calls: list[dict] | None` to `RawResponse`
- Parse `choices[0].message.tool_calls` from API response
- Include `tools` in request payload when provided

**`src/llm/__init__.py`** — `LLM.call()`:
- Add `tools` parameter: `call(messages, tools=None, ...)`
- Add `tool_calls` field to `LLMResult`
- Skip cache when tools present (non-deterministic)

## New modules

**`src/agent/loop.py`** — agent loop:
- `AgentLoop.run(task, tools, ...) -> LoopResult`
- Builds messages: system prompt + history + tool descriptions
- Calls `LLM.call()`, checks for tool_calls, executes, feeds results back
- Guards: `max_steps`, budget check per step, context window limit
- Emits `Event` per step for audit trail

**`src/agent/tools/`** — tool framework:
- `Tool` dataclass: `name, description, parameters (JSON Schema), handler`
- `ToolRegistry`: register, list, execute, generate OpenAI-format definitions
- Tools are sync callables: `(args: dict) -> str`
- Interface matches MCP tool contract for future compatibility

## Tool calling protocol (OpenRouter, verified in docs)

- Request: `tools: [{type: "function", function: {name, description, parameters}}]`
- Response: `choices[0].message.tool_calls: [{id, type, function: {name, arguments}}]`
- Follow-up: `{role: "tool", tool_call_id: "...", content: "result"}`
- `finish_reason: "tool_calls"` when model wants tools
- Both Haiku and Sonnet support tool calling

## Deliverables

### Agent Loop
- [ ] Tool framework (`src/agent/tools/`) — Tool, ToolRegistry
- [ ] Agent loop (`src/agent/loop.py`) — multi-step LLM + tools
- [ ] LLM.call() tool_calls support
- [ ] Built-in tools: echo, budget_status
- [ ] Prompt system (`src/agent/prompts/`) — system prompt + tool composition

### Telegram Bot
- [ ] Public chat: request → agent loop → response
- [ ] Private chat: premium features (subscription model)
- [ ] Channel: scheduled posts, reports, metrics
- [ ] User interaction tracking (likes, messages, payments)
- [ ] Error routing: user-facing / owner-only / self-fixable
- [ ] Bot legend: character, backstory, voice

## Risks

- Tool calling token overhead may be significant with many tools
- Telegram API rate limits
- Multi-step loops can drain budget fast without proper guards
- User retention without clear value proposition

## Gate

Agent loop handles multi-step tasks with tools. Bot operational in public chat.
Channel posts automated. User tracking active.
