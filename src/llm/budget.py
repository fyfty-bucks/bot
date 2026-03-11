"""Budget guard — balance checking, cost recording, predictive alerts.

Alert levels based on estimated days to depletion:
  ok       (>7 days)  — normal operation
  warning  (3-7 days) — alert max 1/day
  critical (1-3 days) — force FAST tier, alert max 1/day
  danger   (0-1 day)  — force FAST tier, alert every call
  depleted (<=0)      — raise BudgetExhausted
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger("agent.llm.budget")

LEVEL_OK = "ok"
LEVEL_WARNING = "warning"
LEVEL_CRITICAL = "critical"
LEVEL_DANGER = "danger"
LEVEL_DEPLETED = "depleted"


@dataclass(frozen=True)
class BudgetStatus:
    """Snapshot of current budget health."""

    balance: float
    daily_burn: float
    days_remaining: float | None
    level: str


class BudgetExhausted(Exception):
    """Raised when balance <= 0. Carries the BudgetStatus that triggered it."""

    def __init__(self, status: BudgetStatus) -> None:
        self.status = status
        super().__init__(
            f"Budget depleted: balance=${status.balance:.2f}, "
            f"burn=${status.daily_burn:.4f}/day"
        )


def check_budget(budget_total: float) -> BudgetStatus:
    """Compute current balance, burn rate, and alert level.

    Burn rate = total LLM spend in last N days / N (N = budget_alert_days).
    Days remaining = balance / daily_burn (None when no spend history).
    """
    raise NotImplementedError


def record_cost(cost: float, model: str, tokens: int) -> None:
    """Record LLM expense in BudgetLog."""
    raise NotImplementedError


def check_alerts(status: BudgetStatus) -> None:
    """Emit budget_alert event if threshold crossed.

    Deduplication: warning/critical emit max 1/day.
    Danger/depleted emit on every call.
    """
    raise NotImplementedError
