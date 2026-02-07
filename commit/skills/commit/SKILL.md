---
name: commit
description: Analyze changes, create conventional commits with smart splitting. Opus analyzes, Haiku executes git commands.
user_invocable: true
arguments:
  - name: push
    description: "Also push to remote after committing"
    required: false
  - name: auto
    description: "Skip confirmation and auto-execute all commits"
    required: false
---

# /commit Skill

Analyze staged/unstaged changes, create conventional commits with smart splitting. You (Opus) analyze and plan; Haiku subagents execute git commands.

## Quick Reference

1. Gather git info (direct, not subagent)
2. Analyze changes → propose commit plan
3. Present commit plan → confirm with user (skip if auto argument provided)
4. Dispatch Haiku subagent(s) to execute git commands
5. Report results; handle hook failures
6. Push if requested

## Phase 1: Analysis (you do this directly)

Run these commands yourself (NOT via subagent):

```bash
git status
git diff
git diff --staged
git log --oneline -5
```

### File scope

If the user specified file paths, directories, or glob patterns in the arguments (e.g., `/commit src/`, `/commit *.py`), restrict the commit scope to only matching files. Still run the full git commands above for context awareness, but only include matching files in the commit plan. Unscoped `/commit` considers all changes.

### Pre-flight checks — stop and report to user if:
- Detached HEAD state
- Merge or rebase in progress
- Unresolved conflicts
- No changes to commit (nothing staged, nothing modified)

### Smart splitting heuristics

Group changes into logical commits when:
- **Unit of work**: a feature/fix and its tests belong in one commit; retroactive test coverage is a separate commit
- **Same file, different intent**: formatting changes, functional changes, and new data entries in the same file should be separate commits (e.g., a `style:` commit for formatting + a `feat:` commit for new content)
- **Different feature areas**: separate modules or components
- **Mixed intent**: refactoring mixed with functional changes
- **When in doubt**: present the split options to the user rather than guessing

### Commit message format

Always use **conventional commits**:
- `feat:` — new feature
- `fix:` — bug fix
- `refactor:` — code restructuring without behavior change
- `test:` — adding or updating tests
- `docs:` — documentation changes
- `chore:` — maintenance, dependencies, config
- `style:` — formatting, whitespace
- `perf:` — performance improvement
- `ci:` — CI/CD changes

Include a scope when obvious: `feat(auth):`, `fix(api):`, etc.

Keep messages concise (1-2 sentences), focused on **why** not **what**.

Use a HEREDOC for the commit message:
```bash
git commit -m "$(cat <<'EOF'
feat(auth): add OAuth2 login flow

Implements Google OAuth2 provider with token refresh.
EOF
)"
```

## Phase 2: Propose Commit Plan

Present the plan to the user:
- For each commit: list files to stage + the commit message
- **ALWAYS present the plan and wait for user confirmation before executing**
- If the `auto` argument was provided, skip confirmation and execute immediately

## Phase 3: Execution (Haiku subagents)

For each commit, dispatch a Haiku subagent:

```
Task tool parameters:
  subagent_type: "commit:commit"
  model: "haiku"
  max_turns: 3
  description: "[commit] execute git add and commit"
  prompt: |
    Run these git commands in sequence:

    1. git add <files>
    2. git commit -m "$(cat <<'EOF'
    <commit message>
    EOF
    )"
```

Execute commits **sequentially** (one subagent at a time), not in parallel.

## Phase 4: Hook Failure Handling

If Haiku reports `HOOK_FAILED`:
1. Read the full hook output
2. Determine what needs to be fixed (linting, formatting, type errors, etc.)
3. Fix the issue yourself (as Opus)
4. Stage the fix and create a **NEW commit** — never amend
5. Dispatch a new Haiku subagent for the retry

## Phase 5: Push (only if requested)

Only push if the user explicitly asked (e.g., `/commit push` or mentioned pushing).

```
Task tool parameters:
  subagent_type: "commit:commit"
  model: "haiku"
  max_turns: 3
  description: "[commit] push to remote"
  prompt: |
    Run: git push
```

Relay the result to the user. If GitHub printed a PR creation URL, highlight it.

## Phase 6: Report Results

Show the user:
- Commit hash(es) and messages for each successful commit
- Any PR URL from push output
- Summary of what was committed

## Safety Rules

**These are non-negotiable:**

- **NEVER** force-push (`git push --force` or `-f`)
- **NEVER** amend commits (`git commit --amend`)
- **NEVER** skip hooks (`--no-verify` or `-n`)
- **NEVER** push unless the user explicitly requested it
- **ALWAYS** create NEW commits after hook failure fixes (never amend the failed one)
- **ALWAYS** use specific file paths with `git add` (never `git add -A` or `git add .`)
- **ALWAYS** use conventional commit format
- **ALWAYS** present commit plan and confirm with user before executing (unless `auto` argument provided)
