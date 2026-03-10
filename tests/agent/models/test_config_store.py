"""Tests for ConfigEntry model."""

import json

from src.agent.models.config_store import ConfigEntry


def test_set_config_value(test_db) -> None:
    """Store and retrieve a config value."""
    ConfigEntry.upsert("model_name", "haiku")
    entry = ConfigEntry.get_by_id("model_name")
    assert entry.get_value() == "haiku"


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
    assert second.get_value() == "sonnet"
    assert second.updated_at >= first_ts


def test_config_json_value(test_db) -> None:
    """Value can be a JSON object."""
    data = {"temp": 0.2, "max_tokens": 1000}
    ConfigEntry.upsert("llm_params", data)

    entry = ConfigEntry.get_by_id("llm_params")
    assert entry.get_value() == data


def test_upsert_string_preserves_type(test_db) -> None:
    """String '42' stored via upsert returns string '42', not int 42."""
    ConfigEntry.upsert("port", "42")
    entry = ConfigEntry.get_by_id("port")
    val = entry.get_value()
    assert val == "42"
    assert isinstance(val, str)
