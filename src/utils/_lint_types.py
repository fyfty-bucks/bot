"""Lint data types — shared across all lint modules."""

from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class LintResult:
    """Single lint check result."""
    path: str
    rule: str
    value: int
    limit: int
    passed: bool
    detail: str = ""
    severity: str = "error"


@dataclass
class FileReport:
    """Lint report for single file."""
    path: Path
    lines: int
    results: list[LintResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)


def is_test_context(path: Path) -> tuple[bool, bool]:
    """Determine test context: (is_test_file, in_tests_dir)."""
    in_tests_dir = any(p == "tests" for p in path.parts)
    is_test_file = path.name.startswith("test_")
    return is_test_file, in_tests_dir
