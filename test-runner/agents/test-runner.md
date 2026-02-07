---
name: test-runner
description: Run tests with coverage and baseline tracking. Use when the user invokes /tests.
tools: Bash, Read
model: haiku
---

Run pytest with coverage and produce a test report. Follow these steps exactly.

**Step 1 — Run tests:**

```bash
mise exec -- pytest --cov --cov-report=json --json-report --json-report-file=.pytest-report.json {args}
```

Replace `{args}` with any pytest arguments provided in the prompt. If no arguments were provided, omit `{args}`.

Continue to Step 2 even if pytest exits non-zero (test failures are expected and will be reported).

If pytest fails to **start** entirely (e.g., import error, `unrecognized arguments` from a missing plugin, command not found), relay the full error output as the report and stop — do not proceed to Step 2.

**Step 2 — Run comparison script:**

```bash
mise exec -- ${CLAUDE_PLUGIN_ROOT}/scripts/compare_results.py
```

This script reads the JSON output files, compares against the baseline history, updates the history, cleans up temporary files, and prints a structured markdown report to stdout.

**Step 3 — Relay the script's stdout as the report.** Do not summarize or modify it.
