# commit Plugin

## Overview
Skill + custom subagent for smart conventional commits with automatic change analysis and splitting. Unlike test-runner (thin skill, heavy subagent), commit is the opposite: the skill is heavy (Opus does analysis, splitting heuristics, commit planning, hook failure handling) and the subagent is thin (Haiku just executes git commands).

## Development

### Structure
- `.claude-plugin/plugin.json` — Plugin manifest
- `agents/commit.md` — Custom haiku subagent (Bash only)
- `skills/commit/SKILL.md` — `/commit` skill with multi-phase workflow

### Testing
```bash
claude --plugin-dir ~/dev/cc-plugins/commit
```

Then invoke `/commit` in a project with changes. Check that:
1. Commit plan is presented for confirmation
2. Commits are created with conventional format
3. `~/.claude/subagent-metrics.jsonl` shows `"subagent_type": "commit"` (if subagent-metrics is loaded)

### Architecture note
The commit plugin uses a heavy-skill/thin-subagent architecture where the skill (running on Opus) handles analysis, splitting heuristics, commit planning, and hook failure handling, while the subagent (running on Haiku) only executes git commands. Metrics integration comes from the custom `commit` subagent type.
