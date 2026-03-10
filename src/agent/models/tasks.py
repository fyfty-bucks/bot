"""Task tracking model — stub for TDD Phase 2."""

import peewee


class Task(peewee.Model):
    """Tracks task lifecycle. Stub — no fields yet."""

    class Meta:
        table_name = "tasks"

    def get_input(self) -> dict:
        """Deserialize input JSON."""
        raise NotImplementedError

    def get_output(self) -> dict | None:
        """Deserialize output JSON."""
        raise NotImplementedError
