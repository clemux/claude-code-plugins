# Plan: Create a `test-runner` plugin with custom subagent

## Context

The `/tests` skill currently lives in `~/.claude/skills/tests/` and dispatches a `general-purpose` haiku subagent. This has two problems:

1. **No skill attribution in metrics** — `subagent-metrics` logs `subagent_type: "general-purpose"`, indistinguishable from other general-purpose calls.
2. **Not distributable** — the skill and its `compare_results.py` script are user-local files, not shareable via the plugin marketplace.

By packaging into a plugin with a dedicated custom subagent, `subagent_type: "test-runner"` becomes the natural skill identifier. The `subagent-metrics` hook already extracts and logs this field (line 15 of `log-subagent-usage.sh`).

The plugin is named generically (`test-runner`) so it can later support JS/TS test runners alongside pytest. The initial implementation is pytest-only.

## New plugin: `test-runner/`

```
test-runner/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   └── test-runner.md           # Custom subagent (haiku, Bash + Read)
├── skills/
│   └── tests/
│       └── SKILL.md              # Skill dispatches to test-runner subagent
├── scripts/
│   └── compare_results.py        # Moved from ~/.claude/skills/tests/
├── CLAUDE.md
└── README.md
```

### 1. `.claude-plugin/plugin.json`

```json
{
  "name": "test-runner",
  "description": "Run tests with coverage and baseline tracking (pytest, with JS/TS support planned)",
  "version": "0.1.0",
  "license": "MIT"
}
```

### 2. `agents/test-runner.md`

```yaml
---
name: test-runner
description: Run tests with coverage and baseline tracking. Use when the user invokes /tests.
tools: Bash, Read
model: haiku
---
```

System prompt (markdown body) contains the workflow currently inlined in the skill's Task prompt:
- Step 1: Run `mise exec -- pytest --cov --cov-report=json --json-report --json-report-file=.pytest-report.json {args}`
- Step 2: Run `mise exec -- python ${CLAUDE_PLUGIN_ROOT}/scripts/compare_results.py`
- Step 3: Relay the script's stdout as the report, unmodified

`${CLAUDE_PLUGIN_ROOT}` resolves in agent markdown, making the script path portable.

### 3. `skills/tests/SKILL.md`

Simplified — no longer inlines the workflow prompt:

```yaml
---
name: tests
description: Run pytest with coverage and baseline tracking. Use when the user invokes /tests.
---
```

Instructions:
1. Extract pytest args from the `/tests` invocation
2. Launch the `test-runner` subagent with a prompt like: `"Run tests with args: {PYTEST_ARGS}"` (or just `"Run tests"` if no args)
3. Relay the result without modification

### 4. `scripts/compare_results.py`

Copy from `~/.claude/skills/tests/compare_results.py` — no changes to the script.

### 5. No changes to `subagent-metrics`

Already logs `subagent_type`. Will now show `"test-runner"` instead of `"general-purpose"`.

## Post-install cleanup

After verifying the plugin works, remove the old user-level skill:
```
rm -r ~/.claude/skills/tests/
```

## Verification

1. Load the plugin: `claude --plugin-dir ~/dev/cc-plugins/test-runner`
2. Invoke `/tests` in a project with pytest
3. Verify the test report is produced correctly
4. Check `~/.claude/subagent-metrics.jsonl` — latest entry should show `"subagent_type": "test-runner"`
5. Both plugins together:
   `claude --plugin-dir ~/dev/cc-plugins/test-runner --plugin-dir ~/dev/cc-plugins/subagent-metrics`
