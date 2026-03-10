"""Tests for Task model."""

import json
from datetime import datetime, timezone

from src.agent.models.tasks import Task


def test_create_task_pending(test_db) -> None:
    """New task is created with pending status."""
    task = Task.create(
        task_type="llm_call",
        input_data=json.dumps({"prompt": "hello"}),
    )
    assert task.status == "pending"
    assert task.completed_at is None
    assert task.error is None


def test_task_lifecycle_complete(test_db) -> None:
    """Task transitions: pending -> running -> completed."""
    task = Task.create(task_type="deploy", input_data="{}")
    assert task.status == "pending"

    task.status = "running"
    task.save()

    task.status = "completed"
    task.completed_at = datetime.now(timezone.utc)
    task.output_data = json.dumps({"result": "ok"})
    task.save()

    loaded = Task.get_by_id(task.id)
    assert loaded.status == "completed"
    assert loaded.completed_at is not None


def test_task_lifecycle_failed(test_db) -> None:
    """Task transitions: pending -> running -> failed with error."""
    task = Task.create(task_type="web_search", input_data="{}")

    task.status = "running"
    task.save()

    task.status = "failed"
    task.error = "ConnectionTimeout: API unreachable"
    task.completed_at = datetime.now(timezone.utc)
    task.save()

    loaded = Task.get_by_id(task.id)
    assert loaded.status == "failed"
    assert "ConnectionTimeout" in loaded.error


def test_task_cost_tracked(test_db) -> None:
    """Task cost is recorded on completion."""
    task = Task.create(task_type="llm_call", input_data="{}")
    task.status = "completed"
    task.cost_usd = 0.005
    task.completed_at = datetime.now(timezone.utc)
    task.save()

    loaded = Task.get_by_id(task.id)
    assert loaded.cost_usd == 0.005


def test_filter_tasks_by_status(test_db) -> None:
    """Filter tasks by status."""
    Task.create(task_type="a", input_data="{}", status="pending")
    Task.create(task_type="b", input_data="{}", status="running")
    Task.create(task_type="c", input_data="{}", status="completed")

    pending = list(Task.select().where(Task.status == "pending"))
    assert len(pending) == 1
    assert pending[0].task_type == "a"


def test_task_input_output_json(test_db) -> None:
    """Input and output round-trip through JSON."""
    inp = {"key": "val", "nested": [1, 2]}
    out = {"result": 42}

    task = Task.create(
        task_type="test",
        input_data=json.dumps(inp),
        output_data=json.dumps(out),
    )

    loaded = Task.get_by_id(task.id)
    assert loaded.get_input() == inp
    assert loaded.get_output() == out
