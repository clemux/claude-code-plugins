# test-runner

A Claude Code plugin that runs pytest with coverage and baseline tracking via the `/tests` command.

## Installation

### From the marketplace

```
/plugin marketplace add clemux/claude-code-plugins
/plugin install test-runner@clemux-claude-code-plugins
```

### From a local clone

```bash
claude --plugin-dir ~/dev/claude-code-plugins/test-runner
```

## Usage

```
/tests                    # Run full test suite
/tests tests/test_auth.py # Run specific file
/tests -k "test_login"   # Run matching tests
```

Any arguments after `/tests` are passed directly to pytest.

## What it does

1. Runs `pytest --cov --cov-report=json --json-report` with any extra arguments
2. Compares results against a local baseline history (`.tests-baseline.json`)
3. Produces a structured markdown report with:
   - Coverage table with deltas from the previous run
   - Coverage trend (last 5 runs)
   - Test summary (passed/failed/error/skipped)
   - New failures with tracebacks
   - Fixed tests
   - Pre-existing failures

## How it works

The `/tests` skill dispatches a dedicated `test-runner` haiku subagent that:

1. Runs pytest via `mise exec` with coverage and JSON reporting plugins
2. Runs `compare_results.py` to analyze results against history
3. Relays the report back unmodified

The custom `test-runner` subagent type enables proper attribution in `subagent-metrics` logs (`"subagent_type": "test-runner"` instead of `"general-purpose"`).

## Dependencies

- `pytest` — test runner
- `pytest-cov` — coverage reporting (`coverage.json`)
- `pytest-json-report` — structured test results (`.pytest-report.json`)
- `mise` — task runner for tool version management

## Files

| File | Purpose |
|------|---------|
| `agents/test-runner.md` | Custom haiku subagent with Bash + Read tools |
| `skills/tests/SKILL.md` | `/tests` slash command that dispatches the subagent |
| `scripts/compare_results.py` | Reads JSON outputs, compares to baseline, prints report |

## Baseline history

Results are stored in `.tests-baseline.json` (up to 10 runs). Add this file to your `.gitignore`.
