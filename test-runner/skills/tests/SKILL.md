---
name: tests
description: Run pytest with coverage and baseline tracking. Use when the user invokes /tests.
---

# /tests — Run Pytest with Coverage & Baseline Tracking

The user has invoked `/tests`. Run the project's test suite with coverage, compare results against a local baseline history, and report regressions, improvements, and trends.

## Instructions

1. Extract pytest arguments (everything after `/tests` in the arguments). These are referred to as `{PYTEST_ARGS}` below.
2. Use the **Task** tool to launch the `test-runner` subagent with a prompt like: `"Run tests with args: {PYTEST_ARGS}"` (or just `"Run tests"` if no args were provided).
3. When the subagent returns, relay its result back to the user **without modification**.
