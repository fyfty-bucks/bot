"""Command registry. Auto-discovers command modules."""

import importlib
import pkgutil
from pathlib import Path
from types import ModuleType


def discover_commands() -> list[ModuleType]:
    """Find all command modules in this package."""
    package_dir = Path(__file__).parent
    modules = []
    for info in pkgutil.iter_modules([str(package_dir)]):
        if info.name.startswith("_"):
            continue
        mod = importlib.import_module(f"src.cli_commands.{info.name}")
        if hasattr(mod, "name") and hasattr(mod, "run"):
            modules.append(mod)
    return modules
