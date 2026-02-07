# subagent-metrics

A Claude Code plugin that logs token usage for every subagent (Task tool) call, enabling cost attribution and skill optimization.

## Installation

### From the marketplace

```
/plugin marketplace add clemux/claude-code-plugins
/plugin install subagent-metrics@clemux-claude-code-plugins
```

### From a local clone

```bash
claude --plugin-dir ~/dev/claude-code-plugins/subagent-metrics
```

## Log format

Each subagent call appends a JSON line to `~/.claude/subagent-metrics.jsonl`:

```json
{
  "ts": "2026-02-07T12:00:00Z",
  "session": "abc123",
  "cwd": "/home/user/my-project",
  "model": "haiku",
  "subagent_type": "general-purpose",
  "skill": "commit",
  "description": "execute git add and commit",
  "total_tokens": 1523,
  "duration_ms": 3200
}
```

## Skill tagging convention

Skills that dispatch subagents should tag the Task `description` with the skill name in brackets:

```
description: "[commit] execute git add and commit"
```

The hook parses the `[...]` prefix as the triggering skill. Untagged calls get `skill: null`.

## Supported analyses

- **Cost attribution**: tokens grouped by triggering skill or project
- **Session profiling**: per-session and per-project token usage
- **Skill optimization**: per-call breakdown within a skill

### Example queries

```bash
# Total tokens by skill
jq -s 'group_by(.skill) | map({skill: .[0].skill, total: map(.total_tokens // 0) | add})' ~/.claude/subagent-metrics.jsonl

# Average tokens per model
jq -s 'group_by(.model) | map({model: .[0].model, avg: (map(.total_tokens // 0) | add / length)})' ~/.claude/subagent-metrics.jsonl
```

## How it works

The plugin registers a PostToolUse hook on the Task tool. After any subagent completes:

1. Extracts `model`, `subagent_type`, `description` from tool input
2. Extracts `cwd` (project path) from the hook event
3. Parses token usage from tool response text (`total_tokens: N`, `duration_ms: N`)
4. Extracts triggering skill from description tag (`[skill-name]` prefix)
5. Atomically appends a JSON log line using `flock`

## Dependencies

- `jq` — for JSON parsing and construction
- `flock` — for atomic file append (standard on Linux)

## Concurrency safety

Uses `flock` for exclusive file locking when appending to the log file, preventing corruption from concurrent subagent completions.
