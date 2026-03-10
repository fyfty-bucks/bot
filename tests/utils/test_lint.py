"""Tests for Python and Markdown analyzers."""

import textwrap
from pathlib import Path

from src.utils.lint import analyze_py, analyze_md


def test_analyze_py_clean(tmp_path: Path) -> None:
    """Clean Python file passes all checks."""
    f = tmp_path / "clean.py"
    f.write_text(textwrap.dedent('''\
        """Module doc."""

        def greet(name: str) -> str:
            return f"hello {name}"
    '''))
    report = analyze_py(f)
    assert report.passed


def test_analyze_py_too_many_lines(tmp_path: Path) -> None:
    """File over 200 lines fails."""
    f = tmp_path / "big.py"
    lines = ['"""Module doc."""\n'] + ["x = 1\n"] * 201
    f.write_text("".join(lines))
    report = analyze_py(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "lines" in rules


def test_analyze_py_no_docstring(tmp_path: Path) -> None:
    """File without module docstring fails."""
    f = tmp_path / "nodoc.py"
    f.write_text("x = 1\n")
    report = analyze_py(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "docstring" in rules


def test_analyze_py_missing_type_hint(tmp_path: Path) -> None:
    """Public function without return type fails type_hints check."""
    f = tmp_path / "notype.py"
    f.write_text(textwrap.dedent('''\
        """Module doc."""

        def greet(name):
            return f"hello {name}"
    '''))
    report = analyze_py(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "type_hints" in rules


def test_analyze_py_private_no_type_hint_ok(tmp_path: Path) -> None:
    """Private function without type hint is fine."""
    f = tmp_path / "private.py"
    f.write_text(textwrap.dedent('''\
        """Module doc."""

        def _helper(x):
            return x + 1
    '''))
    report = analyze_py(f)
    assert report.passed


def test_analyze_py_secret_detected(tmp_path: Path) -> None:
    """Secret pattern in code triggers failure."""
    f = tmp_path / "leak.py"
    f.write_text(textwrap.dedent('''\
        """Module doc."""

        API_KEY = "sk-abc123def456ghi789jkl012mno345"
    '''))
    report = analyze_py(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "secret" in rules


def test_analyze_md_clean(tmp_path: Path) -> None:
    """Short markdown passes."""
    f = tmp_path / "doc.md"
    f.write_text("# Title\n\nContent\n")
    report = analyze_md(f)
    assert report.passed


def test_analyze_md_too_long(tmp_path: Path) -> None:
    """Markdown over 150 lines fails."""
    f = tmp_path / "long.md"
    f.write_text("\n".join(["line"] * 160))
    report = analyze_md(f)
    assert not report.passed


def test_test_file_gets_relaxed_limits(tmp_path: Path) -> None:
    """Test files get 300 line limit, not 200."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    f = tests_dir / "test_something.py"
    lines = ['"""Test module."""\n'] + ["def test_x(): pass\n"] * 250
    f.write_text("".join(lines))
    report = analyze_py(f)
    line_check = [r for r in report.results if r.rule == "lines"][0]
    assert line_check.limit == 300
    assert line_check.passed


def test_analyze_py_nested_function_no_hint_ok(tmp_path: Path) -> None:
    """Nested function inside another function does not need type hint."""
    f = tmp_path / "nested.py"
    f.write_text(textwrap.dedent('''\
        """Module doc."""

        def outer(x: int) -> int:
            def inner(y):
                return y + 1
            return inner(x)
    '''))
    report = analyze_py(f)
    assert report.passed


def test_analyze_py_class_method_needs_hint(tmp_path: Path) -> None:
    """Public class method without return type fails type_hints check."""
    f = tmp_path / "cls.py"
    f.write_text(textwrap.dedent('''\
        """Module doc."""

        class Foo:
            def bar(self):
                return 1
    '''))
    report = analyze_py(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "type_hints" in rules


def test_analyze_py_class_private_method_ok(tmp_path: Path) -> None:
    """Private class method without type hint passes."""
    f = tmp_path / "cls_priv.py"
    f.write_text(textwrap.dedent('''\
        """Module doc."""

        class Foo:
            def _internal(self):
                return 1
    '''))
    report = analyze_py(f)
    assert report.passed


def test_analyze_py_deeply_nested_no_hint_ok(tmp_path: Path) -> None:
    """Function nested inside class method does not need type hint."""
    f = tmp_path / "deep.py"
    f.write_text(textwrap.dedent('''\
        """Module doc."""

        class Foo:
            def bar(self) -> int:
                def helper(x):
                    return x + 1
                return helper(1)
    '''))
    report = analyze_py(f)
    assert report.passed


def test_analyze_py_async_function_needs_hint(tmp_path: Path) -> None:
    """Async public function without return type fails."""
    f = tmp_path / "async_func.py"
    f.write_text(textwrap.dedent('''\
        """Module doc."""

        async def fetch(url: str):
            return url
    '''))
    report = analyze_py(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "type_hints" in rules


def test_analyze_py_too_many_functions(tmp_path: Path) -> None:
    """File with 8 functions fails (src limit=7)."""
    f = tmp_path / "many_funcs.py"
    funcs = "\n".join(f"def fn{i}() -> None:\n    pass\n" for i in range(8))
    f.write_text(f'"""Module doc."""\n\n{funcs}')
    report = analyze_py(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "functions" in rules


def test_analyze_py_too_many_classes(tmp_path: Path) -> None:
    """File with 4 classes fails (src limit=3)."""
    f = tmp_path / "many_cls.py"
    classes = "\n".join(f"class C{i}:\n    pass\n" for i in range(4))
    f.write_text(f'"""Module doc."""\n\n{classes}')
    report = analyze_py(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "classes" in rules


def test_analyze_py_function_too_long(tmp_path: Path) -> None:
    """Function over 50 lines fails func_lines check."""
    f = tmp_path / "long_func.py"
    body = "\n".join(f"    x{i} = {i}" for i in range(50))
    f.write_text(f'"""Module doc."""\n\ndef big() -> None:\n{body}\n')
    report = analyze_py(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "func_lines" in rules


def test_analyze_py_too_many_imports(tmp_path: Path) -> None:
    """File with 16 imports fails (limit=15)."""
    f = tmp_path / "many_imports.py"
    imports = "\n".join(
        f"from os.path import join as j{i}" for i in range(16)
    )
    f.write_text(f'"""Module doc."""\n\n{imports}\n')
    report = analyze_py(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "imports" in rules


def test_analyze_py_syntax_error(tmp_path: Path) -> None:
    """Unparseable Python file returns syntax failure."""
    f = tmp_path / "bad.py"
    f.write_text("def broken(:\n")
    report = analyze_py(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "syntax" in rules


def test_analyze_py_empty_file(tmp_path: Path) -> None:
    """Empty file: 0 lines, no docstring required, passes."""
    f = tmp_path / "empty.py"
    f.write_text("")
    report = analyze_py(f)
    assert report.passed
    assert report.lines == 0


def test_analyze_py_function_count_ignores_nested(tmp_path: Path) -> None:
    """Function count = top-level + class methods only, not nested helpers."""
    f = tmp_path / "nested_many.py"
    f.write_text(textwrap.dedent('''\
        """Module doc."""

        def outer1() -> None:
            def helper1():
                pass
            def helper2():
                pass
            pass

        def outer2() -> None:
            def helper3():
                pass
            pass
    '''))
    report = analyze_py(f)
    func_check = [r for r in report.results if r.rule == "functions"][0]
    assert func_check.value == 2


def test_analyze_py_secret_in_test_file_is_info(tmp_path: Path) -> None:
    """Secret in test file is detected with info severity, not failure."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    f = tests_dir / "test_with_secret.py"
    f.write_text('"""Test."""\n\nFAKE = "sk-abc123def456ghi789jkl012mno345"\n')
    report = analyze_py(f)
    assert report.passed
    info_results = [r for r in report.results if r.severity == "info"]
    assert len(info_results) == 1
    assert info_results[0].rule == "secret"


def test_analyze_md_secret_detected(tmp_path: Path) -> None:
    """Secret pattern in markdown triggers failure."""
    f = tmp_path / "doc.md"
    f.write_text('Config: api_key = "sk-abc123def456ghi789jkl012mno345"\n')
    report = analyze_md(f)
    assert not report.passed
    rules = {r.rule for r in report.results if not r.passed}
    assert "secret" in rules
