# Context Management (Agent Runtime)

## Principle

Context window is the agent's working memory. Every token counts.
**Study the core always, study implementation only when the task requires it.**
Keep core optimized and compact for best context engineering.
Load what's needed, discard what's not, never re-read what's known.

---

## Context Budget

Agent tracks context usage per LLM call:

| Metric | Track |
|--------|-------|
| tokens_in | Input tokens sent |
| tokens_out | Output tokens received |
| context_used_pct | % of model's max context |
| cost | $ per call |

Rule: if context_used_pct > 80%, compress before next call.

---

## Context Assembly (per task)

```
1. CONSTITUTIONAL  — agent_rules/ (always, summarized)
2. TASK            — current task description
3. RELEVANT MEMORY — vector search for similar past tasks
4. CODE CONTEXT    — files relevant to task (read on demand)
5. CONVERSATION    — recent messages (if interactive)
```

Priority: 1 > 2 > 3 > 4 > 5. If window full, drop from bottom.

---

## Compression Strategies

| Strategy | When | How |
|----------|------|-----|
| Summarize | Context > 80% | LLM summarizes conversation so far |
| Drop old | Multi-turn | Keep last N turns, summarize rest |
| Chunk | Large file | Read relevant section, not whole file |
| Cache | Repeated context | Store summaries in memory DB |

---

## Context Injection Patterns

### For deterministic tasks (workflow model)

```
System: You are an executor. Follow instructions exactly.
Rules: [minimal, task-specific rules]
Task: [structured input]
Output format: [strict schema]
```

### For reasoning tasks (smart model)

```
System: You are a reasoning agent. Think step by step.
Constitutional rules: [full agent_rules summary]
Memory: [relevant past experiences]
Task: [open-ended description]
Self-check: Verify your answer against rules before responding.
```

---

## Anti-Patterns

| Bad | Good |
|-----|------|
| Send all agent_rules every call | Summarize, send relevant subset |
| Re-read files already in context | Track loaded context |
| No context budget tracking | Log tokens per call |
| Same prompt for all models | Adapt prompt to model's strengths |
