# Skill: Prompt Generation

Create structured prompts for LLM interactions.

---

## When to Use

- System prompts for agents
- Rules and Skills for agents and IDE like Cursor
- Few-shot examples
- Classification/extraction prompts

---

## Method Selection

| Task | Method | Temperature |
|------|--------|-------------|
| Simple classification | Zero-shot: instruction + format | 0.0 |
| Specific format | Few-shot: 2-5 examples | 0.0 |
| Complex reasoning | Chain-of-thought | 0.2-0.3 |

---

## Prompt Skeleton

```
## Role        — who the model is
## Rules       — numbered constraints
## Task        — specific, measurable
## Input       — data to process
## Output      — expected format (JSON, text, decision)
## Self-Check  — verification before responding
```

---

## Delimiters

| Symbol | Purpose |
|--------|---------|
| `---` | Between blocks |
| `===` | Between examples |
| `"""` | User data |

---

## Anti-Patterns

| Bad | Good |
|-----|------|
| "Tell me about X" | "List 3 facts as JSON" |
| ALL CAPS everywhere | Single NEVER per constraint |
| Vague rules | Specific, testable constraints |
| No output format | Strict schema |
| No self-check | Always verify step at end |

---

## Accuracy Tips

- Ground truth in context
- Temperature 0.0-0.3 for deterministic tasks
- "If unsure: respond with 'Need clarification'"
- Self-check block at end of every prompt

---

## Checklist

- Task at START of prompt?
- Delimiters consistent?
- Examples show exact output format?
- Self-check block present?
