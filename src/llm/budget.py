"""Budget guard — balance checking, cost recording, predictive alerts.

Alert levels based on estimated days to depletion:
  ok       (>7 days)  — normal operation
  warning  (3-7 days) — alert max 1/day
  critical (1-3 days) — force FAST tier, alert max 1/day
  danger   (0-1 day)  — force FAST tier, alert every call
  depleted (<=0)      — raise BudgetExhausted
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

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


def check_budget(budget_total: float, alert_days: int = 7) -> BudgetStatus:
    """Compute current balance, burn rate, and alert level.

    Burn rate = total LLM spend in last N days / N (N = alert_days).
    Days remaining = balance / daily_burn (None when no spend history).
    """
    from src.agent.models.budget import BudgetLog

    last = (
        BudgetLog.select(BudgetLog.balance_after)
        .order_by(BudgetLog.id.desc()).limit(1).first()
    )
    if last is None:
        return BudgetStatus(
            balance=budget_total, daily_burn=0.0,
            days_remaining=None, level=LEVEL_OK,
        )
    balance = last.balance_after
    daily_burn = _compute_burn(alert_days)

    if balance <= 0:
        return BudgetStatus(
            balance=balance, daily_burn=daily_burn,
            days_remaining=0.0, level=LEVEL_DEPLETED,
        )
    if daily_burn == 0:
        return BudgetStatus(
            balance=balance, daily_burn=0.0,
            days_remaining=None, level=LEVEL_OK,
        )
    days = balance / daily_burn
    level = _classify(days)
    return BudgetStatus(
        balance=balance, daily_burn=daily_burn,
        days_remaining=days, level=level,
    )


def _compute_burn(alert_days: int) -> float:
    from src.agent.models.budget import BudgetLog

    cutoff = datetime.now(timezone.utc) - timedelta(days=alert_days)
    total = sum(
        abs(e.amount) for e in
        BudgetLog.select(BudgetLog.amount).where(
            (BudgetLog.category == "llm") & (BudgetLog.created_at >= cutoff),
        )
    )
    return total / alert_days


def _classify(days: float) -> str:
    if days > 7:
        return LEVEL_OK
    if days > 3:
        return LEVEL_WARNING
    if days > 1:
        return LEVEL_CRITICAL
    return LEVEL_DANGER


def record_cost(cost: float, model: str, tokens: int) -> None:
    """Record LLM expense in BudgetLog."""
    from src.agent.models.budget import BudgetLog

    BudgetLog.record(
        amount=-cost, category="llm",
        description=f"{model} {tokens}t",
    )


def check_alerts(status: BudgetStatus) -> None:
    """Emit budget_alert event if threshold crossed.

    Deduplication: warning/critical emit max 1/day.
    Danger/depleted emit on every call.
    """
    from src.agent.models.events import Event

    if status.level == LEVEL_OK:
        return
    payload = {
        "level": status.level,
        "balance": status.balance,
        "daily_burn": status.daily_burn,
        "days_remaining": status.days_remaining,
    }
    if status.level in (LEVEL_DANGER, LEVEL_DEPLETED):
        Event.log("budget_alert", payload)
        return
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )
    for evt in Event.select().where(
        (Event.event_type == "budget_alert") & (Event.created_at >= today),
    ):
        if json.loads(evt.payload).get("level") == status.level:
            return
    Event.log("budget_alert", payload)
