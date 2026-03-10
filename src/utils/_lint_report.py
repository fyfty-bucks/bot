"""Lint report formatter: structured output for LLM + human."""

from src.utils._lint_types import FileReport


def format_report(reports: list[FileReport], verbose: bool = False) -> str:
    """Format lint report: structured for LLM + human readable."""
    lines = ["[LINT] code validator"]
    failed = [r for r in reports if not r.passed]

    if verbose:
        for r in reports:
            tag = "PASS" if r.passed else "FAIL"
            lines.append(f"  {tag}: {r.path} ({r.lines} lines)")
            for x in r.results:
                if not x.passed:
                    detail = f" — {x.detail}" if x.detail else ""
                    lines.append(
                        f"    {x.rule}: {x.value}/{x.limit}{detail}"
                    )
                elif x.severity == "info" and x.detail:
                    lines.append(f"    INFO {x.rule}: {x.detail}")
        lines.append("---")

    total = len(reports)
    ok = total - len(failed)
    lines.append(f"FILES: {total}")
    lines.append(f"PASSED: {ok}")
    lines.append(f"FAILED: {len(failed)}")

    if failed:
        lines.append("---")
        lines.append("FAILURES:")
        for r in failed:
            bad = []
            for x in r.results:
                if not x.passed:
                    detail = f" ({x.detail})" if x.detail else ""
                    bad.append(f"{x.rule}={x.value}{detail}")
            lines.append(f"  {r.path}: {', '.join(bad)}")

    lines.append("---")
    lines.append(f"RESULT: {'OK' if not failed else 'FAIL'}")
    return "\n".join(lines)
