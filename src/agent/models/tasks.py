"""Task tracking model with state machine lifecycle."""

import json
from datetime import datetime, timezone

import peewee


class InvalidTransition(Exception):
    """Raised when a task status transition is not allowed."""


VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"running"},
    "running": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
}


class Task(peewee.Model):
    """Tracks task lifecycle: pending -> running -> completed/failed."""

    task_type = peewee.CharField(max_length=50, index=True)
    status = peewee.CharField(max_length=20, default="pending", index=True)
    input_data = peewee.TextField(default="{}")
    output_data = peewee.TextField(null=True)
    cost_usd = peewee.FloatField(null=True)
    error = peewee.TextField(null=True)
    created_at = peewee.DateTimeField(
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at = peewee.DateTimeField(null=True)

    class Meta:
        table_name = "tasks"

    def get_input(self) -> dict:
        """Deserialize input JSON."""
        return json.loads(self.input_data)

    def get_output(self) -> dict | None:
        """Deserialize output JSON, or None."""
        return json.loads(self.output_data) if self.output_data else None

    def _transition(self, target: str) -> None:
        """Validate and apply a status transition."""
        allowed = VALID_TRANSITIONS.get(self.status, set())
        if target not in allowed:
            raise InvalidTransition(
                f"{self.status} -> {target} is not allowed"
            )
        self.status = target

    def start(self) -> None:
        """Transition pending -> running."""
        self._transition("running")
        self.save()

    def complete(
        self,
        output: dict | None = None,
        cost_usd: float | None = None,
    ) -> None:
        """Transition running -> completed."""
        self._transition("completed")
        self.completed_at = datetime.now(timezone.utc)
        if output is not None:
            self.output_data = json.dumps(output)
        if cost_usd is not None:
            self.cost_usd = cost_usd
        self.save()

    def fail(self, error: str) -> None:
        """Transition running -> failed."""
        self._transition("failed")
        self.completed_at = datetime.now(timezone.utc)
        self.error = error
        self.save()
