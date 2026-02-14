# Claude Code Plugins Marketplace

## Disclaimer

These plugins are just me playing around with Claude Code's plugin system, and have been iteratively developed by prompting Claude Code to improve them each time the behavior didn't match what I had in mind.

There are probably much better-designed plugins that do the same things with more features; if you know of any, please open an issue and I will happily mention them in this README as better alternatives:

- In particular, the **safer-git** plugin should probably be more generic and not be limited to git commands. Hopefully Anthropic will eventually improve the permission system, but in the meantime, I hope there are better plugins than that one.
- The **test-runner** plugin also seems like something interesting that has probably been done better by others -- I'd love to know of such alternatives!

A collection of community plugins for [Claude Code](https://claude.ai/code) that enhance safety, monitoring, and developer experience.

## Installation

### Add this marketplace

```bash
/plugin marketplace add clemux/claude-code-plugins
```

### Install plugins

```bash
# Install the safer-git plugin
/plugin install safer-git@clemux-claude-code-plugins

# Install the subagent-metrics plugin
/plugin install subagent-metrics@clemux-claude-code-plugins
```

## Available Plugins

### safer-git

Blocks dangerous git commands for all agents (main + subagents), preventing accidental data loss and history rewrites. It's called "safer" rather than "safe" because it reduces risk but cannot guarantee complete protection — an LLM agent can find indirect execution paths (scripts, eval, non-Bash runtimes) that bypass command-level hooks. See [known bypass vectors and limitations](safer-git/README.md#agent-bypass-vectors-and-mitigations).

**Protects against:**
- Force pushes (`git push --force`, `--force-with-lease`)
- History rewrites (`git commit --amend`, `git rebase -i`, `git filter-branch`)
- Uncommitted work loss (`git reset --hard`, `git checkout .`, `git clean -f`)
- Hook bypasses (`git commit --no-verify`)
- Stash deletion (`git stash drop`, `git stash clear`)
- Alias-based bypasses (`git config alias.*`)

**How it works:** Registers a PreToolUse hook on the Bash tool that intercepts commands, splits compound statements, and regex-matches each segment against a blocklist. Denies execution with descriptive error messages when dangerous patterns are detected.

**Dependencies:** `jq`, `grep -P` (PCRE support)

[Read more →](safer-git/README.md)

### subagent-metrics

Logs token usage for every subagent (Task tool) call, enabling cost attribution and skill optimization.

**Features:**
- Automatic logging to `~/.claude/subagent-metrics.jsonl`
- Per-skill cost attribution (when skills tag their Task descriptions)
- Session-level profiling with loaded skill sets
- Model usage breakdown (Haiku vs Sonnet)
- Atomic append with `flock` for concurrency safety

**Log fields:** timestamp, session ID, model, subagent type, triggering skill, description, total tokens, duration, loaded skills

**How it works:** Registers a PostToolUse hook on the Task tool that extracts token usage from result text, parses skill tags from descriptions, and appends structured JSON logs.

**Dependencies:** `jq`, `flock`

[Read more →](subagent-metrics/README.md)

### commit

Smart conventional commits with automatic change analysis and splitting via the `/commit` command.

**Features:**
- Analyzes staged and unstaged changes, groups them into logical commits
- Intent-based splitting heuristics with conventional commit messages
- Interactive confirmation before executing (or `auto` mode to skip)
- Pre-commit hook failure handling (fixes issues, creates new commits)
- Optional push after committing

**Usage:** `/commit`, `/commit push`, `/commit auto`

**How it works:** Uses a heavy-skill/thin-subagent architecture — Opus does all analysis, splitting, and planning in the skill, while a dedicated Haiku subagent executes git commands. The custom `commit` subagent type enables proper attribution in subagent-metrics logs.

[Read more →](commit/README.md)

### test-runner

Runs pytest with coverage and baseline tracking via the `/tests` command.

**Features:**
- Coverage table with deltas from previous runs
- Coverage trend (last 5 runs)
- Test summary with new failures, fixed tests, and pre-existing failures
- Structured markdown report
- Baseline history stored in `.tests-baseline.json`

**Usage:** `/tests`, `/tests tests/test_auth.py`, `/tests -k "test_login"`

**How it works:** The `/tests` skill dispatches a dedicated `test-runner` Haiku subagent that runs pytest via `mise exec` with coverage and JSON reporting plugins, then compares results against baseline history.

**Dependencies:** `pytest`, `pytest-cov`, `pytest-json-report`, `mise`

[Read more →](test-runner/README.md)

### worktree

Manages git worktrees using [git gtr](https://github.com/coderabbitai/git-worktree-runner) via the `/worktree` command.

**Features:**
- Create worktrees from any branch, tag, or the current branch
- Copy files (e.g. `.env*`) to worktrees with dry-run preview
- List, remove, and navigate worktrees
- Navigation guidance (terminal, editor, AI session)

**Usage:** `/worktree my-feature`, `/worktree copy my-feature -- ".env*"`, `/worktree list`, `/worktree rm my-feature`

**How it works:** A skill that parses free-form input into intents (create, copy, list, remove, navigate) and runs the corresponding `git gtr` subcommands. Includes safety checks like dry-run previews before copies and confirmation before removal.

**Dependencies:** [git gtr](https://github.com/coderabbitai/git-worktree-runner)

[Read more →](worktree/README.md)

## Marketplace CLI

The `scripts/marketplace.py` script provides a CLI for managing the plugin catalog. It runs as a standalone [uv script](https://docs.astral.sh/uv/guides/scripts/) (no install needed).

```bash
# List all plugins
./scripts/marketplace.py list

# Add a new plugin to the catalog
./scripts/marketplace.py add <plugin-name> --category <category>

# Update a plugin's version in the catalog
./scripts/marketplace.py update-version <plugin-name>

# Sync all marketplace entries with their plugin.json files
./scripts/marketplace.py sync
./scripts/marketplace.py sync --dry-run
```

**Commands:**
- **list** — Display all plugins in a table (name, version, category, description)
- **add** — Register a new plugin directory in the marketplace catalog
- **update-version** — Bump a plugin's version (reads from `plugin.json` by default)
- **sync** — Reconcile marketplace entries with each plugin's `plugin.json` (version, description, license)

## Development

Each plugin is an independent git repository in its own subdirectory. See [CLAUDE.md](CLAUDE.md) for development guidelines and code quality standards.

## License

Each plugin has its own license. See individual plugin directories for details.
