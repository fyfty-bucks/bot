"""Command: agent lint — run code validator."""

import argparse
from pathlib import Path

name = "lint"
help_text = "Run code validator"


def setup(parser: argparse.ArgumentParser) -> None:
    """Configure subparser for this command."""
    parser.add_argument("path", nargs="?", help="File or directory to lint")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show all files")


def run(args: argparse.Namespace) -> int:
    """Execute lint command."""
    from src.utils.lint import lint_path, format_report

    root = Path(".")
    target = Path(args.path) if args.path else root

    reports = lint_path(target, root=root)
    print(format_report(reports, verbose=args.verbose))

    return 0 if all(r.passed for r in reports) else 1
