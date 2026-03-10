"""Command: agent tests — run pytest."""

import argparse
import subprocess
import sys

name = "tests"
help_text = "Run pytest"


def setup(parser: argparse.ArgumentParser) -> None:
    """Configure subparser for this command."""
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")


def run(args: argparse.Namespace) -> int:
    """Execute tests command."""
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    return subprocess.run(cmd).returncode
