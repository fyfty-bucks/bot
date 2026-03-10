"""Key-value configuration store."""

import json
from datetime import datetime, timezone

import peewee


class ConfigEntry(peewee.Model):
    """Persistent key-value config. Values stored as JSON strings."""

    key = peewee.CharField(max_length=100, unique=True, primary_key=True)
    value = peewee.TextField(default="")
    updated_at = peewee.DateTimeField(
        default=lambda: datetime.now(timezone.utc),
    )

    class Meta:
        table_name = "config"

    def get_value(self) -> object:
        """Deserialize JSON value."""
        try:
            return json.loads(self.value)
        except (json.JSONDecodeError, TypeError):
            return self.value

    @classmethod
    def upsert(cls, key: str, value: object) -> "ConfigEntry":
        """Insert or update a config entry atomically."""
        json_val = json.dumps(value)
        now = datetime.now(timezone.utc)
        db = cls._meta.database
        with db.atomic():
            entry, created = cls.get_or_create(
                key=key,
                defaults={"value": json_val, "updated_at": now},
            )
            if not created:
                entry.value = json_val
                entry.updated_at = now
                entry.save()
        return entry
