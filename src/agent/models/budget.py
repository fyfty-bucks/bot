"""Budget tracking model — stub for TDD Phase 2."""

import peewee


class BudgetLog(peewee.Model):
    """Tracks income and expenses. Stub — no fields yet."""

    class Meta:
        table_name = "budget_log"
