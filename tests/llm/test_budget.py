"""Tests for src/llm/budget.py — budget guard and alerts."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from src.agent.models.budget import BudgetLog
from src.agent.models.events import Event
from src.llm import budget as bgt
from src.llm.budget import (
    BudgetStatus,
    check_alerts,
    check_budget,
    record_cost,
)

BUDGET_TOTAL = 50.0


def _spend(amount: float, description: str = "test") -> None:
    """Helper: record a negative BudgetLog entry."""
    BudgetLog.record(amount=-amount, category="llm", description=description)


def _seed_budget(initial: float) -> None:
    """Seed budget with an initial positive balance."""
    BudgetLog.record(amount=initial, category="seed", description="initial")


def test_check_budget_no_history(test_db) -> None:
    """No BudgetLog entries → level='ok', days_remaining=None."""
    status = check_budget(BUDGET_TOTAL)
    assert status.level == bgt.LEVEL_OK
    assert status.days_remaining is None
    assert status.balance == BUDGET_TOTAL


def test_check_budget_ok(test_db) -> None:
    """Balance high relative to burn → level='ok'."""
    _seed_budget(BUDGET_TOTAL)
    _spend(0.01)
    status = check_budget(BUDGET_TOTAL)
    assert status.level == bgt.LEVEL_OK
    assert status.days_remaining is None or status.days_remaining > 7


def test_check_budget_warning(test_db) -> None:
    """3-7 days remaining → level='warning'."""
    _seed_budget(BUDGET_TOTAL)
    _spend(29.0)  # balance=21, burn≈4.1/d → ~5 days remaining
    status = check_budget(BUDGET_TOTAL)
    assert status.level == bgt.LEVEL_WARNING


def test_check_budget_critical(test_db) -> None:
    """1-3 days remaining → level='critical'."""
    _seed_budget(BUDGET_TOTAL)
    _spend(39.0)  # balance=11, burn≈5.6/d → ~2 days remaining
    status = check_budget(BUDGET_TOTAL)
    assert status.level == bgt.LEVEL_CRITICAL


def test_check_budget_danger(test_db) -> None:
    """0-1 days remaining → level='danger'."""
    _seed_budget(BUDGET_TOTAL)
    _spend(47.0)  # balance=3, burn≈6.7/d → ~0.4 days remaining
    status = check_budget(BUDGET_TOTAL)
    assert status.level == bgt.LEVEL_DANGER


def test_check_budget_depleted(test_db) -> None:
    """Balance <= 0 → level='depleted'."""
    _seed_budget(BUDGET_TOTAL)
    _spend(BUDGET_TOTAL + 1.0)
    status = check_budget(BUDGET_TOTAL)
    assert status.level == bgt.LEVEL_DEPLETED
    assert status.balance <= 0


def test_record_cost_creates_budget_log(test_db) -> None:
    """record_cost() creates BudgetLog entry with negative amount."""
    _seed_budget(BUDGET_TOTAL)
    record_cost(cost=0.005, model="openai/gpt-4o-mini", tokens=100)
    last = BudgetLog.select().order_by(BudgetLog.id.desc()).first()
    assert last.amount == -0.005


def test_record_cost_category_is_llm(test_db) -> None:
    """record_cost() uses category='llm'."""
    _seed_budget(BUDGET_TOTAL)
    record_cost(cost=0.003, model="openai/gpt-4o-mini", tokens=50)
    last = BudgetLog.select().order_by(BudgetLog.id.desc()).first()
    assert last.category == "llm"


def test_check_alerts_emits_event_on_warning(test_db) -> None:
    """check_alerts() creates budget_alert event at warning level."""
    status = BudgetStatus(
        balance=10.0, daily_burn=2.0, days_remaining=5.0, level=bgt.LEVEL_WARNING,
    )
    check_alerts(status)

    alerts = list(
        Event.select().where(Event.event_type == "budget_alert"),
    )
    assert len(alerts) == 1
    payload = json.loads(alerts[0].payload)
    assert payload["level"] == bgt.LEVEL_WARNING


def test_check_alerts_deduplicates_daily(test_db) -> None:
    """check_alerts() skips if same level already emitted today."""
    status = BudgetStatus(
        balance=10.0, daily_burn=2.0, days_remaining=5.0, level=bgt.LEVEL_WARNING,
    )
    check_alerts(status)
    check_alerts(status)

    alerts = list(
        Event.select().where(Event.event_type == "budget_alert"),
    )
    assert len(alerts) == 1


def test_check_alerts_danger_always_emits(test_db) -> None:
    """check_alerts() emits danger on every call (no dedup)."""
    status = BudgetStatus(
        balance=1.0, daily_burn=5.0, days_remaining=0.2, level=bgt.LEVEL_DANGER,
    )
    check_alerts(status)
    check_alerts(status)
    check_alerts(status)

    alerts = list(
        Event.select().where(Event.event_type == "budget_alert"),
    )
    assert len(alerts) == 3


def test_check_alerts_ok_emits_nothing(test_db) -> None:
    """check_alerts() does not emit event at ok level."""
    status = BudgetStatus(
        balance=45.0, daily_burn=0.5, days_remaining=90.0, level=bgt.LEVEL_OK,
    )
    check_alerts(status)

    alerts = list(
        Event.select().where(Event.event_type == "budget_alert"),
    )
    assert len(alerts) == 0


def test_check_alerts_deduplicates_critical(test_db) -> None:
    """check_alerts() skips if critical already emitted today."""
    status = BudgetStatus(
        balance=5.0, daily_burn=3.0, days_remaining=1.7, level=bgt.LEVEL_CRITICAL,
    )
    check_alerts(status)
    check_alerts(status)

    alerts = list(
        Event.select().where(Event.event_type == "budget_alert"),
    )
    assert len(alerts) == 1


def test_check_alerts_depleted_always_emits(test_db) -> None:
    """check_alerts() emits depleted on every call (no dedup)."""
    status = BudgetStatus(
        balance=-1.0, daily_burn=10.0, days_remaining=0.0, level=bgt.LEVEL_DEPLETED,
    )
    check_alerts(status)
    check_alerts(status)

    alerts = list(
        Event.select().where(Event.event_type == "budget_alert"),
    )
    assert len(alerts) == 2


def test_record_cost_zero_creates_entry(test_db) -> None:
    """record_cost(0.0) creates BudgetLog entry with zero amount."""
    _seed_budget(BUDGET_TOTAL)
    record_cost(cost=0.0, model="openai/gpt-4o-mini", tokens=0)

    entries = list(BudgetLog.select().where(BudgetLog.category == "llm"))
    assert len(entries) == 1
    assert entries[0].amount == 0.0
    assert entries[0].balance_after == BUDGET_TOTAL


def test_check_alerts_cross_day_reemits(test_db) -> None:
    """Warning emitted yesterday does not block today's warning."""
    yesterday_payload = {
        "level": bgt.LEVEL_WARNING, "balance": 10.0,
        "daily_burn": 2.0, "days_remaining": 5.0,
    }
    event = Event.log("budget_alert", yesterday_payload)
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    Event.update(created_at=yesterday).where(
        Event.id == event.id,
    ).execute()

    status = BudgetStatus(
        balance=10.0, daily_burn=2.0,
        days_remaining=5.0, level=bgt.LEVEL_WARNING,
    )
    check_alerts(status)

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )
    today_alerts = list(
        Event.select().where(
            (Event.event_type == "budget_alert")
            & (Event.created_at >= today_start),
        ),
    )
    assert len(today_alerts) == 1


def test_check_budget_zero_burn_returns_ok(test_db) -> None:
    """All spend outside alert window: burn=0, level=ok, days_remaining=None."""
    _seed_budget(BUDGET_TOTAL)
    entry = BudgetLog.record(amount=-1.0, category="llm", description="old")
    old_date = datetime.now(timezone.utc) - timedelta(days=30)
    BudgetLog.update(created_at=old_date).where(
        BudgetLog.id == entry.id,
    ).execute()

    status = check_budget(BUDGET_TOTAL)

    assert status.level == bgt.LEVEL_OK
    assert status.daily_burn == 0.0
    assert status.days_remaining is None
