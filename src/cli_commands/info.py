"""Command: agent info — show agent overview."""

import argparse

name = "info"
help_text = "Agent overview"


def setup(parser: argparse.ArgumentParser) -> None:
    """Configure subparser for this command."""
    pass


def run(args: argparse.Namespace) -> int:
    """Execute info command."""
    lines = [
        "[INFO] agent overview",
        "PROJECT: 50bucks",
        "DESCRIPTION: autonomous agent on Raspberry Pi 4",
        "BUDGET: $50",
        "---",
        "ENTRY: ./agent <command>",
        "---",
        "RESULT: OK",
    ]
    print("\n".join(lines))
    return 0
