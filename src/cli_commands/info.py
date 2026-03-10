"""Command: agent info — show agent overview with live DB stats."""

import argparse
from pathlib import Path

name = "info"
help_text = "Agent overview with DB stats"


def setup(parser: argparse.ArgumentParser) -> None:
    """Configure subparser for this command."""
    parser.add_argument("--db", default="agent.db", help="Path to agent database")


def _query_stats(db_path: str) -> list[str]:
    """Query DB for event/task/budget stats. Returns formatted lines."""
    from src.agent.db import get_db, create_tables, get_all_models
    from src.agent.models.events import Event
    from src.agent.models.tasks import Task
    from src.agent.models.budget import BudgetLog

    db = get_db(db_path)
    try:
        create_tables(db, get_all_models())
        events = Event.select().count()
        task_counts = {s: Task.select().where(Task.status == s).count()
                       for s in ("pending", "running", "completed", "failed")}
        tasks_str = ", ".join(f"{c} {s}" for s, c in task_counts.items())
        last = (BudgetLog.select(BudgetLog.balance_after)
                .order_by(BudgetLog.id.desc()).limit(1).first())
        balance = last.balance_after if last else 0.0

        return [
            f"DB: {db_path}",
            f"EVENTS: {events}",
            f"TASKS: {tasks_str}",
            f"BALANCE: ${balance:.2f}",
        ]
    finally:
        if not db.is_closed():
            db.close()


def run(args: argparse.Namespace) -> int:
    """Execute info command."""
    lines = [
        "[INFO] agent overview",
        "PROJECT: 50bucks",
        "PHASE: 1 (Core + DB)",
        "---",
    ]

    db_path = args.db
    if Path(db_path).exists():
        lines.extend(_query_stats(db_path))
    else:
        lines.append("DB: not found")

    lines.append("---")
    lines.append("RESULT: OK")
    print("\n".join(lines))
    return 0
