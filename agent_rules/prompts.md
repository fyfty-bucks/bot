# Prompt Engineering (Agent Runtime)

## Principle

Agent constructs prompts for LLM calls. Different tasks need different prompts.
**Structured, minimal, verifiable.**

---

## Prompt Structure

Every LLM call uses this skeleton:

```
## Role
[Who the model is for this task]

## Rules
[Constraints — numbered, specific]

## Task
[What to do — concrete, measurable]

## Input
[Data to process]

## Output Format
[Expected structure — JSON, text, decision]

## Self-Check
[Verification criteria before responding]
```

---

## Method Selection

| Task type | Method | Temperature |
|-----------|--------|-------------|
| Classification, routing | Zero-shot | 0.0 |
| Data extraction | Few-shot (2-3 examples) | 0.0 |
| Code generation | CoT + examples | 0.2 |
| Planning, reasoning | CoT | 0.3 |
| Creative, exploration | Open-ended | 0.5-0.7 |

---

## Prompt Templates (agent manages)

Agent stores prompt templates in `src/agent/prompts/`:

| Template | Purpose |
|----------|---------|
| task_router.txt | Route incoming task to handler |
| code_writer.txt | Generate/modify code |
| self_reflect.txt | Evaluate own performance |
| summarize.txt | Compress context |
| research.txt | Web search + synthesis |

Templates are versionable. Agent MAY improve them (self-improvement cycle).

---

## Optimization

- Measure: tokens used, accuracy, latency per template
- A/B test: run variant prompts, compare metrics
- Shortest effective prompt wins (saves tokens = saves money)
- Cache effective prompts in memory DB

---

## Anti-Patterns

| Bad | Good |
|-----|------|
| "Tell me about X" | "List 3 facts about X as JSON" |
| Vague role | Specific role with constraints |
| No output format | Strict schema |
| No self-check | Always verify step |
| Same prompt for cheap and smart model | Adapt complexity to model |
