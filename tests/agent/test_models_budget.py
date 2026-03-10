"""Tests for BudgetLog model."""

from src.agent.models.budget import BudgetLog


def test_create_budget_entry(test_db) -> None:
    """Basic budget entry creation and retrieval."""
    entry = BudgetLog.create(
        amount=-0.003,
        category="llm",
        description="haiku call",
        balance_after=49.997,
    )
    loaded = BudgetLog.get_by_id(entry.id)
    assert loaded.amount == -0.003
    assert loaded.category == "llm"
    assert loaded.description == "haiku call"


def test_budget_balance_after(test_db) -> None:
    """balance_after reflects remaining balance."""
    BudgetLog.create(
        amount=-0.003,
        category="llm",
        description="first call",
        balance_after=49.997,
    )
    loaded = BudgetLog.select().first()
    assert loaded.balance_after == 49.997


def test_budget_negative_is_expense(test_db) -> None:
    """Negative amount represents an expense."""
    entry = BudgetLog.create(
        amount=-0.01, category="api", description="api call",
        balance_after=49.99,
    )
    assert entry.amount < 0


def test_budget_positive_is_income(test_db) -> None:
    """Positive amount represents income."""
    entry = BudgetLog.create(
        amount=1.50, category="telegram", description="user payment",
        balance_after=51.50,
    )
    assert entry.amount > 0


def test_budget_total_spent(test_db) -> None:
    """SUM of negative amounts gives total spent."""
    import peewee

    expenses = [(-0.003, 49.997), (-0.01, 49.987), (-0.005, 49.982)]
    for amount, balance in expenses:
        BudgetLog.create(
            amount=amount, category="llm",
            description="call", balance_after=balance,
        )
    BudgetLog.create(
        amount=1.0, category="income",
        description="payment", balance_after=50.982,
    )

    total = (
        BudgetLog
        .select(peewee.fn.SUM(BudgetLog.amount))
        .where(BudgetLog.amount < 0)
        .scalar()
    )
    assert abs(total - (-0.018)) < 1e-9


def test_budget_filter_by_category(test_db) -> None:
    """Filter budget entries by category."""
    BudgetLog.create(
        amount=-0.01, category="llm",
        description="a", balance_after=49.99,
    )
    BudgetLog.create(
        amount=-0.02, category="api",
        description="b", balance_after=49.97,
    )
    BudgetLog.create(
        amount=-0.01, category="llm",
        description="c", balance_after=49.96,
    )

    llm_entries = list(
        BudgetLog.select().where(BudgetLog.category == "llm")
    )
    assert len(llm_entries) == 2
