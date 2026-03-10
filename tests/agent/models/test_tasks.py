"""Tests for Task model — lifecycle state machine."""

import json

import pytest

from src.agent.models.tasks import Task, InvalidTransition


def test_create_task_pending(test_db) -> None:
    """New task is created with pending status."""
    task = Task.create(
        task_type="llm_call",
        input_data=json.dumps({"prompt": "hello"}),
    )
    assert task.status == "pending"
    assert task.completed_at is None
    assert task.error is None


def test_start_transitions_to_running(test_db) -> None:
    """start() moves task from pending to running."""
    task = Task.create(task_type="deploy", input_data="{}")
    task.start()

    loaded = Task.get_by_id(task.id)
    assert loaded.status == "running"


def test_complete_sets_timestamp_and_output(test_db) -> None:
    """complete() sets status, completed_at, output_data, and cost."""
    task = Task.create(task_type="deploy", input_data="{}")
    task.start()
    task.complete(output={"result": "ok"}, cost_usd=0.005)

    loaded = Task.get_by_id(task.id)
    assert loaded.status == "completed"
    assert loaded.completed_at is not None
    assert loaded.get_output() == {"result": "ok"}
    assert loaded.cost_usd == 0.005


def test_complete_without_output(test_db) -> None:
    """complete() works without output or cost."""
    task = Task.create(task_type="cleanup", input_data="{}")
    task.start()
    task.complete()

    loaded = Task.get_by_id(task.id)
    assert loaded.status == "completed"
    assert loaded.completed_at is not None
    assert loaded.get_output() is None


def test_fail_sets_timestamp_and_error(test_db) -> None:
    """fail() sets status, completed_at, and error message."""
    task = Task.create(task_type="web_search", input_data="{}")
    task.start()
    task.fail(error="ConnectionTimeout: API unreachable")

    loaded = Task.get_by_id(task.id)
    assert loaded.status == "failed"
    assert loaded.completed_at is not None
    assert "ConnectionTimeout" in loaded.error


def test_complete_from_pending_raises(test_db) -> None:
    """Cannot complete a task that hasn't started."""
    task = Task.create(task_type="llm_call", input_data="{}")
    with pytest.raises(InvalidTransition):
        task.complete()


def test_fail_from_pending_raises(test_db) -> None:
    """Cannot fail a task that hasn't started."""
    task = Task.create(task_type="llm_call", input_data="{}")
    with pytest.raises(InvalidTransition):
        task.fail(error="nope")


def test_start_from_completed_raises(test_db) -> None:
    """Cannot restart a completed task."""
    task = Task.create(task_type="llm_call", input_data="{}")
    task.start()
    task.complete()
    with pytest.raises(InvalidTransition):
        task.start()


def test_start_twice_raises(test_db) -> None:
    """Cannot start an already running task."""
    task = Task.create(task_type="llm_call", input_data="{}")
    task.start()
    with pytest.raises(InvalidTransition):
        task.start()


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


def test_task_empty_input(test_db) -> None:
    """Task with empty input_data default works."""
    task = Task.create(task_type="health_check")
    assert task.get_input() == {}


def test_terminal_states_explicit() -> None:
    """Terminal states (completed, failed) are explicit keys in VALID_TRANSITIONS."""
    from src.agent.models.tasks import VALID_TRANSITIONS
    assert "completed" in VALID_TRANSITIONS
    assert "failed" in VALID_TRANSITIONS
    assert VALID_TRANSITIONS["completed"] == set()
    assert VALID_TRANSITIONS["failed"] == set()
