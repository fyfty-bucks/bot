"""Agent CLI — modular router. Auto-discovers commands."""

import argparse
import sys


def main() -> int:
    """CLI entry point. Discovers and routes to command modules."""
    from src.cli_commands import discover_commands

    parser = argparse.ArgumentParser(
        prog="agent",
        description="Autonomous agent CLI",
    )
    sub = parser.add_subparsers(dest="cmd")

    commands = {}
    for mod in discover_commands():
        p = sub.add_parser(mod.name, help=getattr(mod, "help_text", ""))
        if hasattr(mod, "setup"):
            mod.setup(p)
        commands[mod.name] = mod.run

    args = parser.parse_args()

    if args.cmd in commands:
        return commands[args.cmd](args)

    parser.print_help()
    return 2
