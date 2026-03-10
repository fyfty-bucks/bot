"""Lint core: Python/Markdown analyzers, AST checks."""

import ast
from pathlib import Path

from src.utils._lint_config import PY_LIMITS, TEST_LIMITS, MD_LIMITS
from src.utils._lint_types import LintResult, FileReport, is_test_context
from src.utils._lint_secrets import check_secrets

_TEST_INFRA = {"conftest.py", "_helpers.py"}


def _extract_metrics(tree: ast.Module) -> tuple[list[str], int, int, int, bool]:
    """Extract lint metrics from parsed AST.

    Returns (class_names, func_count, max_func_lines, imports, has_docstring).
    func_count = top-level + class methods (module API surface).
    max_func_lines = longest function at any depth (complexity check).
    """
    classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]

    func_count = 0
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_count += 1
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_count += 1

    max_func_lines = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            size = node.end_lineno - node.lineno + 1
            if size > max_func_lines:
                max_func_lines = size

    imports = sum(
        len(n.names) for n in tree.body
        if isinstance(n, (ast.Import, ast.ImportFrom))
    )
    has_doc = (
        bool(tree.body)
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    )
    return classes, func_count, max_func_lines, imports, has_doc


def _check_type_hints(tree: ast.Module, path: str) -> list[LintResult]:
    """Check public functions have return type annotation.

    Checks module-level functions and class methods only.
    """
    missing = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_") and node.returns is None:
                missing.append(node.name)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not item.name.startswith("_") and item.returns is None:
                        missing.append(item.name)
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
    lines = len(content.splitlines())
    p = str(path)

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return FileReport(path, lines, [LintResult(p, "syntax", 0, 0, False)])

    classes, func_count, max_func, imports, has_doc = _extract_metrics(tree)
    is_test, in_tests = is_test_context(path)

    if is_test or (path.name in _TEST_INFRA and in_tests):
        lim = TEST_LIMITS
    else:
        lim = PY_LIMITS

    results = [
        LintResult(p, "lines", lines, lim["lines"], lines <= lim["lines"]),
        LintResult(p, "functions", func_count, lim["functions"],
                   func_count <= lim["functions"]),
        LintResult(p, "classes", len(classes), lim["classes"],
                   len(classes) <= lim["classes"]),
        LintResult(p, "func_lines", max_func, lim["func_lines"],
                   max_func <= lim["func_lines"]),
        LintResult(p, "imports", imports, lim["imports"],
                   imports <= lim["imports"]),
        LintResult(p, "docstring", 1 if has_doc else 0, 1,
                   has_doc or lines == 0),
    ]
    results.extend(_check_type_hints(tree, p))
    results.extend(check_secrets(content, path))
    return FileReport(path, lines, results)


def analyze_md(path: Path) -> FileReport:
    """Analyze Markdown/MDC file."""
    content = path.read_text(encoding="utf-8")
    lines = len(content.splitlines())
    p = str(path)
    results = [
        LintResult(p, "lines", lines, MD_LIMITS["lines"],
                   lines <= MD_LIMITS["lines"]),
    ]
    results.extend(check_secrets(content, path))
    return FileReport(path, lines, results)
