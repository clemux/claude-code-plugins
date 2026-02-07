# Claude Code Plugins Marketplace

A collection of community plugins for [Claude Code](https://claude.ai/code) that enhance safety, monitoring, and developer experience.

## Installation

### Add this marketplace

```bash
/plugin marketplace add <github-owner>/cc-plugins
```

### Install plugins

```bash
# Install the safer-git plugin
/plugin install safer-git@cc-plugins

# Install the subagent-metrics plugin
/plugin install subagent-metrics@cc-plugins
```

## Available Plugins

### safer-git

Blocks dangerous git commands for all agents (main + subagents), preventing accidental data loss and history rewrites.

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

## Development

Each plugin is an independent git repository in its own subdirectory. See [CLAUDE.md](CLAUDE.md) for development guidelines and code quality standards.

## License

Each plugin has its own license. See individual plugin directories for details.
