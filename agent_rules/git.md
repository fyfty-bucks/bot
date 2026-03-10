# Git Rules (Agent on RPi)

## Principle

Agent works in `agent` branch. Pulls core updates from `main`.
**Never write to `main` or `dev`.**

---

## Branch Model

```
main                    # Stable. Consensus merges only.
├── dev                 # Developer's branch. Agent: don't touch.
└── agent               # Agent's primary branch.
    ├── agent/skills    # Sub-branch for skill work (optional)
    └── agent/evolve-N  # Sub-branch for evolution cycle N
```

### Branch Limits

- Max 3 agent sub-branches at a time
- Merge sub-branches back to `agent` when done
- Delete merged sub-branches immediately
- If 3 exist, finish one before creating new

---

## Agent Workflow

### Self-Improvement

```
1. git checkout agent (or agent/evolve-N for isolation)
2. Write tests → implement → validate → harden
3. git add . && git commit -m "agent: description"
4. git push origin agent
5. Append to CHANGELOG.md
```

### Pulling Core Updates (from `main`)

```
1. git fetch origin main
2. Compare: git log agent..origin/main --oneline
3. If new commits:
   a. git merge origin/main
   b. If conflict → abort, notify developer
   c. If clean → run tests
   d. If tests pass → restart service
   e. If tests fail → git revert, notify developer
```

### Schedule

- Check main for updates: every 5 minutes
- Self-improvement: max 1 cycle per session

---

## Commit Rules

- Commit only after tests pass
- One commit per logical change
- Batch related changes into single commit
- Never force-push
- Never write to `main` or `dev`

---

## Commit Format

```
agent: description

Changes: brief list
Tests: passed
```

---

## File Ownership

Agent MAY modify:
- `src/skills/`
- `src/agent/prompts/`
- `src/agent/config/` (values, not structure)
- `tests/agent_tests/` (agent's own tests)
- `agent_rules/runtime/` (runtime constitution)
- `CHANGELOG.md` (append only)

Agent MUST NOT modify:
- `src/agent/core.py`, `src/cli.py`, `src/utils/`
- `.cursor/` (Opus rules)
- `agent_rules/core-constitution.md`
- `tests/` root and `tests/utils/`, `tests/crypto/` (developer tests)

---

## Conflict Resolution

Agent does NOT resolve conflicts. Ever.

```
If merge conflict:
  1. git merge --abort
  2. Log: which files conflicted
  3. Notify developer
  4. Continue on current agent HEAD
```

---

## Merge to Main

Agent cannot merge to main. Process:

```
1. Agent pushes to agent branch
2. Developer reviews changes
3. Consensus: developer + model review
4. Developer merges agent → main
```
