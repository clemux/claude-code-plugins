# subagent-metrics Plugin

## Overview
PostToolUse hook that logs token usage for every Task tool call to `~/.claude/subagent-metrics.jsonl`.

## Development

### Structure
- `.claude-plugin/plugin.json` — Plugin manifest
- `hooks/hooks.json` — Hook configuration (PostToolUse on Task)
- `hooks/log-subagent-usage.sh` — Token usage logger

### Skill tagging convention
Skills that dispatch subagents should tag the Task `description` with the skill name in brackets:
```
description: "[commit] execute git add and commit"
```
The hook parses the `[...]` prefix as the triggering skill. Untagged calls get `skill: null`.

### Testing
```bash
claude --plugin-dir ~/dev/cc-plugins/subagent-metrics
```
Then dispatch any subagent and check `~/.claude/subagent-metrics.jsonl`.

### Code quality
- Run `shellcheck hooks/log-subagent-usage.sh` before committing
- Requires `jq` at runtime
