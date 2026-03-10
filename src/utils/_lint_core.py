"""Lint core: data types, Python/Markdown analyzers, AST checks."""

import ast
import re
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


@dataclass
class FileReport:
    """Lint report for single file."""
    path: Path
    lines: int
    results: list[LintResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)


PY_LIMITS = {
    "lines": 200, "functions": 7, "classes": 3,
    "func_lines": 50, "imports": 15,
}
TEST_LIMITS = {
    "lines": 300, "functions": 25, "classes": 5,
    "func_lines": 50, "imports": 15,
}
MD_LIMITS = {"lines": 150}

_TEST_INFRA = {"conftest.py", "_helpers.py"}

_SECRET_PATTERNS = [
    re.compile(r'sk-[a-zA-Z0-9]{20,}'),
    re.compile(r'0x[a-fA-F0-9]{40,}'),
    re.compile(r'(?i)password\s*=\s*["\'][^"\']+["\']'),
    re.compile(r'(?i)private[_\s]?key\s*=\s*["\'][^"\']+["\']'),
    re.compile(r'(?i)secret\s*=\s*["\'][^"\']+["\']'),
    re.compile(r'(?i)api[_\s]?key\s*=\s*["\'][^"\']+["\']'),
]


def _is_test_file(path: Path) -> bool:
    """Check if file is a test file (skip secret scanning)."""
    parts = path.parts
    return path.name.startswith("test_") or any(p == "tests" for p in parts)


def _check_secrets(content: str, path: Path) -> list[LintResult]:
    """Scan for leaked secret patterns. Skips test files."""
    if _is_test_file(path):
        return []
    hits = []
    p = str(path)
    for i, line in enumerate(content.splitlines(), 1):
        for pat in _SECRET_PATTERNS:
            if pat.search(line):
                hits.append(LintResult(
                    p, "secret", i, 0, False,
                    f"line {i}: possible secret ({pat.pattern[:30]}...)",
                ))
    return hits


def _parse_py(content: str) -> tuple[list, list, int, bool]:
    """Parse Python AST: returns (classes, func_sizes, imports, has_docstring)."""
    tree = ast.parse(content)
    classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
    func_sizes = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_sizes.append(node.end_lineno - node.lineno + 1)
    imports = sum(
        len(n.names) for n in ast.walk(tree)
        if isinstance(n, (ast.Import, ast.ImportFrom))
    )
    has_doc = (
        bool(tree.body)
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    )
    return classes, func_sizes, imports, has_doc


def _check_type_hints(content: str, path: str) -> list[LintResult]:
    """Check public functions have return type annotation."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    missing = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith("_"):
            continue
        if node.returns is None:
            missing.append(node.name)
    if missing:
        names = ", ".join(missing[:5])
        suffix = f" +{len(missing)-5}" if len(missing) > 5 else ""
        return [LintResult(
            path, "type_hints", len(missing), 0, False,
            f"missing return type: {names}{suffix}",
        )]
    return []


def analyze_py(path: Path) -> FileReport:
    """Analyze Python file against coding standards."""
    content = path.read_text(encoding="utf-8")
    lines = content.rstrip("\n").count("\n") + 1 if content else 0
    p = str(path)

    try:
        classes, func_sizes, imports, has_doc = _parse_py(content)
    except SyntaxError:
        return FileReport(path, lines, [LintResult(p, "syntax", 0, 0, False)])

    max_func = max(func_sizes) if func_sizes else 0
    parts = path.parts
    in_tests = any(part == "tests" for part in parts)

    if path.name.startswith("test_") or (path.name in _TEST_INFRA and in_tests):
        lim = TEST_LIMITS
    else:
        lim = PY_LIMITS

    results = [
        LintResult(p, "lines", lines, lim["lines"], lines <= lim["lines"]),
        LintResult(p, "functions", len(func_sizes), lim["functions"],
                   len(func_sizes) <= lim["functions"]),
        LintResult(p, "classes", len(classes), lim["classes"],
                   len(classes) <= lim["classes"]),
        LintResult(p, "func_lines", max_func, lim["func_lines"],
                   max_func <= lim["func_lines"]),
        LintResult(p, "imports", imports, lim["imports"],
                   imports <= lim["imports"]),
        LintResult(p, "docstring", 1 if has_doc else 0, 1,
                   has_doc or lines == 0),
    ]
    results.extend(_check_type_hints(content, p))
    results.extend(_check_secrets(content, path))
    return FileReport(path, lines, results)


def analyze_md(path: Path) -> FileReport:
    """Analyze Markdown/MDC file."""
    content = path.read_text(encoding="utf-8")
    lines = content.rstrip("\n").count("\n") + 1 if content else 0
    p = str(path)
    results = [
        LintResult(p, "lines", lines, MD_LIMITS["lines"],
                   lines <= MD_LIMITS["lines"]),
    ]
    results.extend(_check_secrets(content, path))
    return FileReport(path, lines, results)
