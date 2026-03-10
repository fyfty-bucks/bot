"""Tests for ConfigEntry model."""

import json

from src.agent.models.config_store import ConfigEntry


def test_set_config_value(test_db) -> None:
    """Store and retrieve a config value."""
    ConfigEntry.upsert("model_name", "haiku")
    entry = ConfigEntry.get_by_id("model_name")
    assert entry.value == "haiku"


def test_get_config_missing_returns_none(test_db) -> None:
    """Missing key returns None, not an exception."""
    entry = ConfigEntry.get_or_none(ConfigEntry.key == "nonexistent")
    assert entry is None


def test_update_config_value(test_db) -> None:
    """Updating existing key changes value and updated_at."""
    ConfigEntry.upsert("model_name", "haiku")
    first = ConfigEntry.get_by_id("model_name")
    first_ts = first.updated_at

    ConfigEntry.upsert("model_name", "sonnet")
    second = ConfigEntry.get_by_id("model_name")
    assert second.value == "sonnet"
    assert second.updated_at >= first_ts


def test_config_json_value(test_db) -> None:
    """Value can be a JSON object."""
    data = {"temp": 0.2, "max_tokens": 1000}
    ConfigEntry.upsert("llm_params", data)

    entry = ConfigEntry.get_by_id("llm_params")
    assert entry.get_value() == data


def test_config_key_is_unique(test_db) -> None:
    """Upsert with same key overwrites previous value."""
    ConfigEntry.upsert("key1", "first")
    ConfigEntry.upsert("key1", "second")

    count = ConfigEntry.select().where(ConfigEntry.key == "key1").count()
    assert count == 1

    entry = ConfigEntry.get_by_id("key1")
    assert entry.value == "second"
