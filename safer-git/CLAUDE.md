# safer-git Plugin

## Overview
PreToolUse hook that blocks dangerous git commands for both the main agent and subagents.

## Development

### Structure
- `.claude-plugin/plugin.json` — Plugin manifest
- `hooks/hooks.json` — Hook configuration (PreToolUse on Bash)
- `hooks/guard-git.sh` — Command guard script

### Testing
```bash
claude --plugin-dir ~/dev/cc-plugins/safer-git
```

Then try blocked commands (should be denied) and safe commands (should pass).

### Code quality
- Run `shellcheck hooks/guard-git.sh` before committing
- Requires `jq` at runtime
