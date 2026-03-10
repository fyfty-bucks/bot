"""Key-value configuration store — stub for TDD Phase 2."""

import peewee


class ConfigEntry(peewee.Model):
    """Persistent key-value config. Stub — no fields yet."""

    class Meta:
        table_name = "config"

    def get_value(self) -> object:
        """Deserialize JSON value."""
        raise NotImplementedError

    @classmethod
    def upsert(cls, key: str, value: object) -> "ConfigEntry":
        """Insert or update a config entry."""
        raise NotImplementedError
