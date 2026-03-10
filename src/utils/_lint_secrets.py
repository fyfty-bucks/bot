"""Lint secret scanner — detects leaked credentials in source files."""

import re
from pathlib import Path

from src.utils._lint_types import LintResult, is_test_context

_SECRET_PATTERNS = [
    re.compile(r'sk-[a-zA-Z0-9]{20,}'),
    re.compile(r'0x[a-fA-F0-9]{40,}'),
    re.compile(r'(?i)password\s*=\s*["\'][^"\']+["\']'),
    re.compile(r'(?i)private[_\s]?key\s*=\s*["\'][^"\']+["\']'),
    re.compile(r'(?i)secret\s*=\s*["\'][^"\']+["\']'),
    re.compile(r'(?i)api[_\s]?key\s*=\s*["\'][^"\']+["\']'),
    re.compile(r'AKIA[0-9A-Z]{16}'),
    re.compile(r'ghp_[a-zA-Z0-9]{36,}'),
    re.compile(r'gho_[a-zA-Z0-9]{36,}'),
    re.compile(r'github_pat_[a-zA-Z0-9_]{22,}'),
]


def check_secrets(content: str, path: Path) -> list[LintResult]:
    """Scan for leaked secret patterns. Info-level in test files."""
    _, in_tests = is_test_context(path)
    hits = []
    p = str(path)
    for i, line in enumerate(content.splitlines(), 1):
        for pat in _SECRET_PATTERNS:
            if pat.search(line):
                hits.append(LintResult(
                    p, "secret", i, 0,
                    passed=in_tests,
                    detail=f"line {i}: possible secret ({pat.pattern[:30]}...)",
                    severity="info" if in_tests else "error",
                ))
    return hits
