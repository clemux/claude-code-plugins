#!/usr/bin/env python3
"""Compare pytest + coverage results against a local baseline history.

Reads:
  - coverage.json        (pytest-cov output)
  - .pytest-report.json  (pytest-json-report output)
  - .tests-baseline.json (run history, if exists)

Outputs:
  - Structured markdown report to stdout
  - Updates .tests-baseline.json with the current run
  - Deletes coverage.json and .pytest-report.json after processing
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

COVERAGE_FILE = "coverage.json"
PYTEST_REPORT_FILE = ".pytest-report.json"
BASELINE_FILE = ".tests-baseline.json"
MAX_HISTORY = 10


def load_json(path: str) -> dict | None:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse {path}: {e}", file=sys.stderr)
        return None


def extract_coverage(data: dict) -> dict:
    totals = data.get("totals", {})
    return {
        "percent_covered": round(totals.get("percent_covered", 0), 1),
        "covered_lines": totals.get("covered_lines", 0),
        "missing_lines": totals.get("missing_lines", 0),
        "num_statements": totals.get("num_statements", 0),
    }


def extract_tests(data: dict) -> dict:
    summary = data.get("summary", {})
    failed_tests = []
    failure_details = {}

    for test in data.get("tests", []):
        outcome = test.get("outcome", "")
        nodeid = test.get("nodeid", "")
        if outcome in ("failed", "error"):
            failed_tests.append(nodeid)
            call = test.get("call", {})
            detail = {}
            if call.get("longrepr"):
                detail["traceback"] = call["longrepr"]
            if call.get("stdout"):
                detail["stdout"] = call["stdout"]
            if call.get("stderr"):
                detail["stderr"] = call["stderr"]
            if detail:
                failure_details[nodeid] = detail

    return {
        "total": summary.get("total", 0),
        "passed": summary.get("passed", 0),
        "failed": summary.get("failed", 0),
        "error": summary.get("error", 0),
        "skipped": summary.get("skipped", 0),
        "failed_tests": failed_tests,
        "failure_details": failure_details,
    }


def format_delta(current: float | int, previous: float | int | None, is_percent: bool = False) -> str:
    if previous is None:
        return "—"
    delta = current - previous
    if delta == 0:
        return "0"
    sign = "+" if delta > 0 else ""
    if is_percent:
        return f"{sign}{delta:.1f}%"
    return f"{sign}{delta}"


def build_report(coverage: dict, tests: dict, previous: dict | None) -> list[str]:
    lines = []
    lines.append("## Test Report")
    lines.append("")

    prev_cov = previous.get("coverage") if previous else None
    prev_tests = previous.get("tests") if previous else None

    # Coverage table
    lines.append("### Coverage")
    lines.append("| Metric | Current | Delta |")
    lines.append("|---|---|---|")
    lines.append(f"| Coverage | {coverage['percent_covered']}% | {format_delta(coverage['percent_covered'], prev_cov.get('percent_covered') if prev_cov else None, is_percent=True)} |")
    lines.append(f"| Covered lines | {coverage['covered_lines']} | {format_delta(coverage['covered_lines'], prev_cov.get('covered_lines') if prev_cov else None)} |")
    lines.append(f"| Missing lines | {coverage['missing_lines']} | {format_delta(coverage['missing_lines'], prev_cov.get('missing_lines') if prev_cov else None)} |")
    lines.append(f"| Statements | {coverage['num_statements']} | {format_delta(coverage['num_statements'], prev_cov.get('num_statements') if prev_cov else None)} |")
    lines.append("")

    return lines


def build_trend(history: list[dict]) -> list[str]:
    if len(history) < 2:
        return []
    # History is newest-first; reverse for chronological display
    recent = list(reversed(history[:5]))
    trend_values = [f"{run['coverage']['percent_covered']}%" for run in recent]
    lines = []
    lines.append(f"### Coverage Trend (last {len(recent)} runs)")
    lines.append(" → ".join(trend_values))
    lines.append("")
    return lines


def build_test_summary(tests: dict) -> list[str]:
    lines = []
    lines.append("### Test Summary")
    lines.append("| Status | Count |")
    lines.append("|---|---|")
    lines.append(f"| Passed | {tests['passed']} |")
    lines.append(f"| Failed | {tests['failed']} |")
    lines.append(f"| Error | {tests['error']} |")
    lines.append(f"| Skipped | {tests['skipped']} |")
    lines.append("")
    return lines


def build_failure_sections(tests: dict, previous: dict | None) -> list[str]:
    lines = []
    current_failures = set(tests["failed_tests"])
    prev_failures = set(previous["tests"]["failed_tests"]) if previous and "tests" in previous else set()
    details = tests.get("failure_details", {})

    new_failures = current_failures - prev_failures
    fixed_tests = prev_failures - current_failures
    preexisting = current_failures & prev_failures

    if new_failures:
        lines.append("### New Failures")
        for nodeid in sorted(new_failures):
            lines.append(f"#### {nodeid}")
            if nodeid in details:
                d = details[nodeid]
                if "traceback" in d:
                    lines.append("```")
                    lines.append(d["traceback"])
                    lines.append("```")
                if "stdout" in d:
                    lines.append("**stdout:**")
                    lines.append("```")
                    lines.append(d["stdout"])
                    lines.append("```")
                if "stderr" in d:
                    lines.append("**stderr:**")
                    lines.append("```")
                    lines.append(d["stderr"])
                    lines.append("```")
            lines.append("")

    if fixed_tests:
        lines.append("### Fixed Tests")
        for nodeid in sorted(fixed_tests):
            lines.append(f"- {nodeid}")
        lines.append("")

    if preexisting:
        lines.append("### Pre-existing Failures")
        for nodeid in sorted(preexisting):
            lines.append(f"#### {nodeid}")
            if nodeid in details:
                d = details[nodeid]
                if "traceback" in d:
                    lines.append("```")
                    lines.append(d["traceback"])
                    lines.append("```")
                if "stdout" in d:
                    lines.append("**stdout:**")
                    lines.append("```")
                    lines.append(d["stdout"])
                    lines.append("```")
                if "stderr" in d:
                    lines.append("**stderr:**")
                    lines.append("```")
                    lines.append(d["stderr"])
                    lines.append("```")
            lines.append("")

    return lines


def check_gitignore() -> list[str]:
    lines = []
    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        if BASELINE_FILE not in content:
            lines.append("### Warnings")
            lines.append(f"- `{BASELINE_FILE}` is not in `.gitignore`")
            lines.append("")
    else:
        lines.append("### Warnings")
        lines.append(f"- No `.gitignore` found — consider adding `{BASELINE_FILE}` to it")
        lines.append("")
    return lines


def main():
    # Check for required input files
    missing = []
    if not os.path.exists(COVERAGE_FILE):
        missing.append(f"`{COVERAGE_FILE}` — install pytest-cov: `pip install pytest-cov`")
    if not os.path.exists(PYTEST_REPORT_FILE):
        missing.append(f"`{PYTEST_REPORT_FILE}` — install pytest-json-report: `pip install pytest-json-report`")

    if missing:
        print("## Test Report")
        print()
        print("**Error:** Required output files are missing:")
        print()
        for m in missing:
            print(f"- {m}")
        print()
        print("Make sure the required pytest plugins are installed and the test run completed.")
        sys.exit(1)

    # Load data
    cov_data = load_json(COVERAGE_FILE)
    test_data = load_json(PYTEST_REPORT_FILE)

    if cov_data is None or test_data is None:
        print("Error: Failed to read test output files.", file=sys.stderr)
        sys.exit(1)

    coverage = extract_coverage(cov_data)
    tests = extract_tests(test_data)

    # Load history
    baseline = load_json(BASELINE_FILE)
    if baseline is None:
        baseline = {"runs": []}

    history = baseline.get("runs", [])
    previous = history[0] if history else None

    # Build current run record (without failure_details — too large for history)
    current_run = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "coverage": coverage,
        "tests": {
            "total": tests["total"],
            "passed": tests["passed"],
            "failed": tests["failed"],
            "error": tests["error"],
            "skipped": tests["skipped"],
            "failed_tests": tests["failed_tests"],
        },
    }

    # Build report
    report = []
    report.extend(build_report(coverage, tests, previous))
    report.extend(build_trend([current_run] + history))
    report.extend(build_test_summary(tests))
    report.extend(build_failure_sections(tests, previous))
    report.extend(check_gitignore())

    if previous is None:
        report.append("*First run — baseline established.*")
        report.append("")

    # Update history (newest first, max 10)
    history.insert(0, current_run)
    baseline["runs"] = history[:MAX_HISTORY]

    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=2)
        f.write("\n")

    # Cleanup temp files
    for path in (COVERAGE_FILE, PYTEST_REPORT_FILE):
        try:
            os.remove(path)
        except OSError:
            pass

    # Output report
    print("\n".join(report))


if __name__ == "__main__":
    main()
