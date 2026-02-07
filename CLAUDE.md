# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository overview

This is a marketplace of Claude Code plugins managed as a monorepo. The `marketplace.json` file at the repository root serves as the source of truth for the plugin catalog. Each subdirectory is an independent plugin, and the repository uses shared tooling for linting, validation, and versioning.

### Plugins

- **safer-git** — PreToolUse hook that blocks dangerous git commands (force-push, reset --hard, amend, etc.) for all agents including subagents. Intercepts Bash tool calls, splits compound commands, and regex-matches each segment against a blocklist.
- **subagent-metrics** — PostToolUse hook that logs token usage for every Task tool call to `~/.claude/subagent-metrics.jsonl`. Parses skill tags from description brackets (`[skill-name]`), extracts token counts from tool results, and appends atomically with `flock`.

## Plugin anatomy

Each plugin follows this structure:
```
plugin-name/
  .claude-plugin/plugin.json   # Manifest: name + description
  hooks/hooks.json              # Hook registration (event type, tool matcher, command)
  hooks/<script>.sh             # Hook implementation (bash, reads JSON from stdin)
  CLAUDE.md                     # Plugin-specific dev notes
  README.md                     # Usage docs
```

Key conventions:
- Hooks receive JSON on stdin with `tool_input` (and `tool_result` for PostToolUse)
- PreToolUse hooks deny by writing `{"permissionDecision":"deny","systemMessage":"..."}` to stderr and exiting 2
- PostToolUse hooks are non-blocking (exit 0, no transcript output)
- `${CLAUDE_PLUGIN_ROOT}` in hooks.json resolves to the plugin directory at runtime

## Development workflow

### Setup

Install pre-commit hooks and tooling:
```bash
prek install
```

### Code quality

Run linting across all plugins:
```bash
mise run lint
```

Validate plugin manifests and marketplace.json:
```bash
mise run validate
```

Individual plugin shellcheck:
```bash
shellcheck safer-git/hooks/guard-git.sh
shellcheck subagent-metrics/hooks/log-subagent-usage.sh
```

### Committing changes

Use commitizen for standardized commit messages:
```bash
cz commit
```

When bumping plugin versions, use commitizen's bump command in the plugin directory:
```bash
cd <plugin-name>
cz bump
```

## Testing

Each plugin is tested by loading it into a Claude Code session:
```bash
claude --plugin-dir ~/dev/cc-plugins/<plugin-name>
```
There are no automated test suites — testing is manual (trigger the relevant tool and verify behavior).

## Marketplace structure

The repository root contains:
- **marketplace.json** — Catalog of all available plugins (source of truth)
- **.mise.toml** — Task runner configuration for lint/validate commands
- **.pre-commit-config.yaml** — Git hooks for automated checks
- **pyproject.toml** — Commitizen configuration for conventional commits

## Runtime dependencies

All hook scripts require `jq` for JSON parsing. The safer-git plugin also requires `grep -P` (PCRE support).

Development dependencies (managed by mise/prek):
- `jq` — JSON parsing in hook scripts
- `shellcheck` — Shell script linting
- `commitizen` — Conventional commit enforcement
- `pre-commit` — Git hook management
