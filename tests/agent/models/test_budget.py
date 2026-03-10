"""Tests for BudgetLog model — CRUD basics + record() with auto-balance."""

from datetime import datetime

import peewee as pw

from src.agent.models.budget import BudgetLog


def test_create_budget_entry_direct(test_db) -> None:
    """Direct create() stores and retrieves all fields correctly."""
    entry = BudgetLog.create(
        amount=-0.01, category="llm",
        description="test call", balance_after=49.99,
    )
    loaded = BudgetLog.get_by_id(entry.id)
    assert loaded.amount == -0.01
    assert loaded.category == "llm"
    assert loaded.description == "test call"
    assert loaded.balance_after == 49.99
    assert isinstance(loaded.created_at, datetime)


def test_budget_model_defaults(test_db) -> None:
    """Default description is empty string, created_at is auto-set."""
    entry = BudgetLog.create(
        amount=50.0, category="initial", balance_after=50.0,
    )
    assert entry.description == ""
    assert entry.created_at is not None


def test_record_creates_entry(test_db) -> None:
    """record() creates a budget entry with correct fields."""
    entry = BudgetLog.record(
        amount=-0.003, category="llm", description="haiku call",
    )
    loaded = BudgetLog.get_by_id(entry.id)
    assert loaded.amount == -0.003
    assert loaded.category == "llm"
    assert loaded.description == "haiku call"


def test_record_first_entry_starts_from_zero(test_db) -> None:
    """First record computes balance_after from zero."""
    entry = BudgetLog.record(amount=50.0, category="initial", description="seed")
    assert entry.balance_after == 50.0


def test_record_auto_calculates_balance(test_db) -> None:
    """Subsequent records compute balance from previous entry."""
    BudgetLog.record(amount=50.0, category="initial", description="seed")
    entry = BudgetLog.record(amount=-0.003, category="llm", description="call")
    assert abs(entry.balance_after - 49.997) < 1e-9


def test_record_chain_computes_correctly(test_db) -> None:
    """Chain of records produces correct running balance."""
    BudgetLog.record(amount=50.0, category="initial", description="seed")
    BudgetLog.record(amount=-0.003, category="llm", description="call 1")
    BudgetLog.record(amount=-0.01, category="llm", description="call 2")
    entry = BudgetLog.record(amount=-0.005, category="llm", description="call 3")
    assert abs(entry.balance_after - 49.982) < 1e-9


def test_total_spent_via_sum(test_db) -> None:
    """SUM of negative amounts gives total spent."""
    BudgetLog.record(amount=50.0, category="initial", description="seed")
    BudgetLog.record(amount=-0.003, category="llm", description="call")
    BudgetLog.record(amount=-0.01, category="llm", description="call")
    BudgetLog.record(amount=-0.005, category="llm", description="call")
    BudgetLog.record(amount=1.0, category="income", description="payment")

    total = (
        BudgetLog
        .select(pw.fn.SUM(BudgetLog.amount))
        .where(BudgetLog.amount < 0)
        .scalar()
    )
    assert abs(total - (-0.018)) < 1e-9


def test_filter_by_category(test_db) -> None:
    """Filter budget entries by category."""
    BudgetLog.record(amount=-0.01, category="llm", description="a")
    BudgetLog.record(amount=-0.02, category="api", description="b")
    BudgetLog.record(amount=-0.01, category="llm", description="c")

    llm_entries = list(
        BudgetLog.select().where(BudgetLog.category == "llm")
    )
    assert len(llm_entries) == 2


def test_record_zero_amount(test_db) -> None:
    """Zero amount is valid (e.g. adjustment entry)."""
    BudgetLog.record(amount=50.0, category="initial", description="seed")
    entry = BudgetLog.record(amount=0.0, category="adjust", description="noop")
    assert entry.balance_after == 50.0


def test_record_empty_description(test_db) -> None:
    """Empty description is allowed (default)."""
    entry = BudgetLog.record(amount=50.0, category="initial")
    assert entry.description == ""
