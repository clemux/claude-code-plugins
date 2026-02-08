# test-runner Plugin

## Overview
Skill + custom subagent that runs pytest with coverage, compares against a baseline history, and reports regressions, improvements, and trends.

## Development

### Structure
- `.claude-plugin/plugin.json` — Plugin manifest
- `agents/test-runner.md` — Custom haiku subagent (Bash only)
- `skills/tests/SKILL.md` — `/tests` skill dispatches to the subagent
- `scripts/compare_results.py` — Baseline comparison and report generation

### Testing
```bash
claude --plugin-dir ~/dev/cc-plugins/test-runner
```

Then invoke `/tests` in a project with pytest configured. Check that:
1. The test report is produced correctly
2. `.tests-baseline.json` is created/updated
3. `~/.claude/subagent-metrics.jsonl` shows `"subagent_type": "test-runner"` (if subagent-metrics is loaded)

### Runtime dependencies
- `pytest`, `pytest-cov`, `pytest-json-report` — test execution and output
- `python3` — for `compare_results.py`
- `mise` — task runner (wraps pytest and python invocations)
