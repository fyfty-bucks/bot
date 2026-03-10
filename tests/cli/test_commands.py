"""Tests for CLI command routing and discovery."""

from io import StringIO
from unittest.mock import patch

from src.cli import main


def _run_main(*args: str) -> tuple[int, str]:
    """Run main() with patched sys.argv, return (exit_code, stdout)."""
    argv = ["agent"] + list(args)
    out = StringIO()
    with patch("sys.argv", argv), patch("sys.stdout", out):
        code = main()
    return code, out.getvalue()


def test_no_args_shows_help_with_commands() -> None:
    """No arguments prints help (exit 2) listing all discovered commands."""
    code, output = _run_main()
    assert code == 2
    assert "usage" in output.lower()
    assert "lint" in output
    assert "tests" in output


def test_info_command_runs() -> None:
    """info command executes and returns 0."""
    code, output = _run_main("info")
    assert code == 0
    assert "50bucks" in output


def test_info_no_db_shows_not_found() -> None:
    """info without DB shows 'not found' and still returns 0."""
    code, output = _run_main("info", "--db", "/tmp/_no_such_agent.db")
    assert code == 0
    assert "not found" in output.lower()
    assert "RESULT: OK" in output


def test_info_with_db_shows_stats(tmp_path) -> None:
    """info with populated DB shows event/task/budget counts."""
    from src.agent.db import get_db, create_tables, get_all_models
    from src.agent.models.events import Event
    from src.agent.models.tasks import Task
    from src.agent.models.budget import BudgetLog

    db_path = str(tmp_path / "test_info.db")
    db = get_db(db_path)
    create_tables(db, get_all_models())

    Event.log("test_event", {"msg": "hello"})
    Event.log("test_event", {"msg": "world"})
    task = Task.create(task_type="demo", input_data="{}")
    task.start()
    task.complete(output={"ok": True})
    Task.create(task_type="pending_demo", input_data="{}")
    BudgetLog.record(50.0, "initial", "seed budget")
    BudgetLog.record(-2.50, "llm", "haiku call")

    db.close()

    code, output = _run_main("info", "--db", db_path)
    assert code == 0
    assert "EVENTS: 2" in output
    assert "BALANCE: $47.50" in output
    assert "completed" in output.lower()
    assert "pending" in output.lower()
    assert "RESULT: OK" in output

