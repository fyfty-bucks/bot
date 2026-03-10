# Runtime Autonomy (agent-modifiable)

Extends core-constitution.md with tunable parameters.
Agent MAY modify this file through self-improvement cycles.

---

## Resource Thresholds

| Resource | Warn | Critical | Action |
|----------|------|----------|--------|
| RAM | 6GB used | 7GB | Kill non-essential, report |
| Disk | 80% full | 90% | Clean caches, report |
| Temperature | 70°C | 80°C | Reduce load, report |
| API budget | 80% spent | 95% | Reduce to Fast-only, report |

---

## Operational Parameters

| Parameter | Value | Modifiable |
|-----------|-------|------------|
| Main check interval | 5 minutes | Yes |
| Max evolution cycles/session | 1 | Yes |
| Max agent sub-branches | 3 | Yes |
| Spike budget (API calls) | 5 | Yes |
| Spike timeout | 10 minutes | Yes |
| Implement max retries | 3 | Yes |
| Heartbeat interval | 30 minutes | Yes |

---

## Heartbeat Report

Agent periodically reports:
- Uptime, CPU temp, RAM/disk usage
- API budget remaining
- Tasks completed since last report
- Errors encountered
- Active branches count

---

## Self-Modification Log

Every change to this file must be logged:

```
CHANGELOG entry:
  agent: autonomy — changed [parameter] from [old] to [new]
  Reason: [metric-based justification]
```
