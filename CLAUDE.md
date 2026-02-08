# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository overview

This is a marketplace of Claude Code plugins managed as a monorepo. The `.claude-plugin/marketplace.json` file serves as the source of truth for the plugin catalog. Each subdirectory is an independent plugin, and the repository uses shared tooling for linting, validation, and versioning.

### Plugins

- **safer-git** — PreToolUse hook that blocks dangerous git commands (force-push, reset --hard, amend, etc.) for all agents including subagents. Intercepts Bash tool calls, splits compound commands, and regex-matches each segment against a blocklist.
- **subagent-metrics** — PostToolUse hook that logs token usage for every Task tool call to `~/.claude/subagent-metrics.jsonl`. Parses skill tags from description brackets (`[skill-name]`), extracts token counts from tool results, and appends atomically with `flock`. Includes a `metrics.py` CLI (uv script) for querying logs, aggregating stats, and listing sessions.
- **commit** — Skill + custom subagent for smart conventional commits. Opus analyzes changes, applies intent-based splitting heuristics, and proposes a commit plan; a thin Haiku subagent executes git commands. Invoked via `/commit`.
- **test-runner** — Skill + custom subagent for running pytest with coverage and baseline tracking. The `/tests` skill dispatches a dedicated Haiku subagent that runs pytest with coverage and JSON reporting, then compares results against baseline history.
- **worktree** — Skill for managing git worktrees using git gtr. Creates worktrees, copies files, and guides the user to navigate or start AI sessions in them. Invoked via `/worktree`.

## Plugin anatomy

Every plugin has a manifest; other components are optional depending on what the plugin does.

```
plugin-name/
  .claude-plugin/plugin.json        # Required — manifest (name, description, version, license)
  hooks/hooks.json                   # Hook registration (event type, tool matcher, command)
  hooks/<script>.sh                  # Hook implementation (bash, reads JSON from stdin)
  skills/<skill-name>/SKILL.md       # Skill definition (user-invocable slash command)
  agents/<agent-name>.md             # Custom subagent (system prompt + model/tools config)
  scripts/<script>.py                # Supporting scripts (e.g. comparison, analysis)
  .cz.toml                          # Commitizen config (version tracking, tag format)
  CLAUDE.md                          # Plugin-specific dev notes
  README.md                          # Usage docs
```

### Hooks
- Hooks receive JSON on stdin with `tool_input` (and `tool_result` for PostToolUse)
- PreToolUse hooks deny by writing `{"permissionDecision":"deny","systemMessage":"..."}` to stderr and exiting 2
- PostToolUse hooks are non-blocking (exit 0, no transcript output)

### Skills
- Defined in `skills/<name>/SKILL.md` with YAML frontmatter (name, description, arguments)
- User-invocable via `/<skill-name>` slash commands
- Can dispatch custom subagents via the Task tool

### Agents
- Defined in `agents/<name>.md` with YAML frontmatter (model, tools, description)
- Referenced as `<plugin-name>:<agent-name>` in `subagent_type`
- Typically thin executors (e.g. Haiku for git commands) paired with a heavier skill

### General
- `${CLAUDE_PLUGIN_ROOT}` in hooks.json and agent/skill files resolves to the plugin directory at runtime

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

Run ruff (fast linter + formatter check):
```bash
ruff check .
```

Run pylint:
```bash
pylint subagent-metrics/metrics.py test-runner/scripts/compare_results.py
```

When validating or parsing JSON files, use `jq` instead of Python scripts for easier auditing
```bash
jq empty <file.json>                  # validate
jq '.version' plugin.json             # extract a field
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

### Commit type guidelines

Plugin components are **functionality**, not documentation. Use the commit type that matches the intent of the change:

- `feat:` — new capability (new skill, new hook, new agent, new script)
- `fix:` — improving or correcting existing behavior (fixing a SKILL.md workflow, hook logic, agent prompt)
- `refactor:` — restructuring without behavior change (reorganizing a SKILL.md, renaming agents)
- `docs:` — changes to README.md, CLAUDE.md, or other non-functional documentation only

In particular, changes to `SKILL.md`, `agents/*.md`, `hooks/*.sh`, and `scripts/*.py` are almost never `docs:` — they change how the plugin behaves.

## Testing

Each plugin is tested by loading it into a Claude Code session:
```bash
claude --plugin-dir ~/dev/cc-plugins/<plugin-name>
```
There are no automated test suites — testing is manual (trigger the relevant tool and verify behavior).

### Updating plugins in the marketplace

The `scripts/marketplace.py` script (standalone [uv script](https://docs.astral.sh/uv/guides/scripts/)) manages the `marketplace.json` catalog.

Sync all marketplace entries with their `plugin.json` files (updates version, description, license):
```bash
./scripts/marketplace.py sync
./scripts/marketplace.py sync --dry-run  # preview changes without writing
```

Update a single plugin's version:
```bash
./scripts/marketplace.py update-version <plugin-name>          # reads version from plugin.json
./scripts/marketplace.py update-version <plugin-name> -v 1.2.0  # explicit version
```

Add a new plugin to the catalog:
```bash
./scripts/marketplace.py add <plugin-name> --category <category>
```

List all plugins:
```bash
./scripts/marketplace.py list
```

## Marketplace structure

The repository root contains:
- **.claude-plugin/marketplace.json** — Catalog of all available plugins (source of truth)
- **.mise.toml** — Task runner configuration for lint/validate commands
- **.pre-commit-config.yaml** — Git hooks for automated checks
- **pyproject.toml** — Commitizen configuration for conventional commits

## Runtime dependencies

All hook scripts require `jq` for JSON parsing. The safer-git plugin also requires `grep -P` (PCRE support). The subagent-metrics plugin also requires `flock` for atomic file appends.

Development dependencies (managed by mise/prek):
- `jq` — JSON parsing in hook scripts
- `shellcheck` — Shell script linting
- `ruff` — Python linting (runs in pre-commit and `mise run lint`)
- `pylint` — Python linting (runs only via `mise run lint`, too slow for pre-commit)
- `commitizen` — Conventional commit enforcement
- `prek` — Git hook management
