---
name: worktree
description: Manage git worktrees using git gtr — create, copy files, list, remove, and navigate. Use when the user invokes /worktree.
user_invocable: true
---

# /worktree — Manage Git Worktrees with `git gtr`

The user has invoked `/worktree`. Help them manage git worktrees using the `git gtr` CLI (git worktree runner).

## Pre-flight

Before running any `git gtr` command, verify it is installed:

```bash
git gtr version
```

If the command fails, tell the user:

> `git gtr` is not installed. Install it from https://github.com/coderabbitai/git-worktree-runner

Do NOT proceed with any worktree operations until `git gtr` is available.

## Parse intent

Interpret the user's free-form input after `/worktree` and map it to one of these intents:

| User says                                                    | Intent                                        |
|--------------------------------------------------------------|-----------------------------------------------|
| `/worktree my-feature`                                       | **create** a worktree for branch `my-feature` |
| `/worktree new my-feature --from-current`                    | **create** with options                       |
| `/worktree copy my-feature -- ".env*"`                       | **copy** files to a worktree                  |
| `/worktree list` or `/worktree ls`                           | **list** worktrees                            |
| `/worktree rm my-feature` or `/worktree remove my-feature`   | **remove** a worktree                         |
| `/worktree go my-feature` or `/worktree navigate my-feature` | **navigate** guidance                         |

If the intent is ambiguous, ask the user to clarify.

## Creating worktrees

Run `git gtr new <branch>` with any options the user specified.

Common options:
- `--from <ref>` — create from a specific branch/tag/commit
- `--from-current` — create from the current branch (for parallel variants)
- `--no-copy` — skip copying configured files to the new worktree
- `--no-fetch` — skip `git fetch` before creation
- `-e, --editor` — open in editor after creation
- `-a, --ai` — start AI tool after creation

Example:
```bash
git gtr new my-feature
git gtr new my-feature --from-current
git gtr new my-feature --from main --no-copy
```

After successful creation, tell the user how to access the worktree:
- Open in editor: `git gtr editor my-feature`
- Start AI session: `git gtr ai my-feature`
- Navigate in terminal: `cd "$(git gtr go my-feature)"`

## Copying files

Use `git gtr copy <target> [-- <pattern>...]` to copy files from the main repo to a worktree.

**Always preview first** with `--dry-run` before copying, unless the user explicitly asks to skip the preview:
```bash
git gtr copy my-feature --dry-run -- ".env*"
```

Then run without `--dry-run` to execute:
```bash
git gtr copy my-feature -- ".env*"
```

Useful variations:
- Copy using configured patterns: `git gtr copy my-feature`
- Copy specific patterns: `git gtr copy my-feature -- ".env*" "*.json"`
- Copy to all worktrees: `git gtr copy --all -- ".env*"`
- Copy from a different worktree: `git gtr copy my-feature --from other-branch`

## Listing worktrees

```bash
git gtr list
```

Show the output to the user.

## Removing worktrees

**Always ask the user for confirmation before removing a worktree.**

Present the command you will run:
```bash
git gtr rm my-feature
```

Optional flags (only use if the user requests):
- `--delete-branch` — also delete the git branch
- `--force` — force removal of a dirty worktree

Do NOT use `--force` unless the user explicitly asks for it.

## Navigation guidance

The agent cannot `cd` into a worktree — it is anchored to the current project directory. Instead, tell the user how to navigate:

- **Terminal**: `cd "$(git gtr go my-feature)"`
- **Editor**: `git gtr editor my-feature`
- **AI session**: `git gtr ai my-feature`
- **Run a command in the worktree**: `git gtr run my-feature <command>`

If the user wants to run a one-off command in the worktree, use `git gtr run`:
```bash
git gtr run my-feature git status
git gtr run my-feature npm test
```

## Safety rules

1. Always verify `git gtr` is installed before running commands
2. Use `--dry-run` to preview copy operations before executing
3. Always confirm with the user before `git gtr rm`
4. Never use `--force` on `rm` unless the user explicitly requests it
5. Never use `--yes` to skip confirmations — let the user review
