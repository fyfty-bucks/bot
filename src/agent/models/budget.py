"""Budget tracking model with auto-balance computation."""

from datetime import datetime, timezone

import peewee


class BudgetLog(peewee.Model):
    """Tracks every income and expense. Negative amount = expense."""

    amount = peewee.FloatField()
    category = peewee.CharField(max_length=30, index=True)
    description = peewee.TextField(default="")
    balance_after = peewee.FloatField()
    created_at = peewee.DateTimeField(
        default=lambda: datetime.now(timezone.utc),
    )

    class Meta:
        table_name = "budget_log"

    @classmethod
    def record(
        cls,
        amount: float,
        category: str,
        description: str = "",
    ) -> "BudgetLog":
        """Create entry with auto-computed balance_after."""
        db = cls._meta.database
        with db.atomic():
            last = (
                cls.select(cls.balance_after)
                .order_by(cls.id.desc())
                .limit(1)
                .first()
            )
            prev_balance = last.balance_after if last else 0.0
            return cls.create(
                amount=amount,
                category=category,
                description=description,
                balance_after=prev_balance + amount,
            )
