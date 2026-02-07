# commit

A Claude Code plugin for smart conventional commits with automatic change analysis and splitting via the `/commit` command.

## Installation

```bash
claude --plugin-dir ~/dev/cc-plugins/commit
```

## Usage

```
/commit          # Analyze changes, propose commits, execute after confirmation
/commit push     # Same, then push to remote
/commit auto     # Skip confirmation, auto-execute commits
```

## What it does

1. Analyzes staged and unstaged changes (git status, diff, log)
2. Groups changes into logical commits using intent-based splitting heuristics
3. Proposes a commit plan with conventional commit messages
4. Presents the plan for user confirmation (unless `auto` is used)
5. Dispatches haiku subagents to execute git add + commit
6. Handles pre-commit hook failures (fixes issues, creates new commits)
7. Pushes if requested

## How it works

Unlike test-runner (thin skill, heavy subagent), commit inverts the pattern:

- The `/commit` **skill** is heavy: Opus does all analysis, splitting heuristics, commit planning, and hook failure handling
- The `commit` **subagent** is thin: Haiku just executes git commands and reports structured results (OK/HOOK_FAILED/ERROR)

The custom `commit` subagent type enables proper attribution in `subagent-metrics` logs.

## Safety rules

- Never force-push, amend, or skip hooks
- Never push unless explicitly requested
- Always uses specific file paths (never `git add .`)
- Always uses conventional commit format
- Always confirms with user before executing (unless `auto`)

## Files

| File | Purpose |
|------|---------|
| `agents/commit.md` | Custom haiku subagent (Bash only) for git execution |
| `skills/commit/SKILL.md` | `/commit` slash command with multi-phase workflow |
