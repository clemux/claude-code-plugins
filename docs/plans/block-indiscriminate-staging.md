# Plan: Block Indiscriminate Staging Commands in safer-git Plugin

## Context

Commands that automatically stage large numbers of files without explicit selection are risky in dirty repositories:

- **`git add -A` / `git add --all`**: Stages all changes including untracked files. Can bloat commits with build artifacts, local configs, or sensitive data.
- **`git commit -a` / `git commit --all`**: Automatically stages all modified and deleted tracked files before committing. Bypasses explicit staging review and can include unintended changes.

These commands are particularly dangerous when used by autonomous agents that may not verify what they're staging. The safer-git plugin already blocks other dangerous git operations by pattern-matching commands in the PreToolUse hook. We'll extend this blocklist to include both patterns.

## Implementation

**File to modify:** `/home/clemux/dev/cc-plugins/safer-git/hooks/guard-git.sh`

Add two new patterns and descriptions to the existing arrays (insert after line 31, before the "Discard uncommitted work" section):

1. **Add to PATTERNS array**:
   ```bash
   # Indiscriminate staging (risks bloated/unintended commits)
   'git\s+add\s+(-A|--all)\b'
   'git\s+commit\s+.*(-a|--all)\b'
   ```

2. **Add to DESCRIPTIONS array** (corresponding positions):
   ```
   "Add all files including untracked (risks bloated commits)"
   "Commit with auto-stage -a (bypasses explicit staging review)"
   ```

Pattern details (PCRE syntax):
- `git\s+add\s+(-A|--all)\b` matches "git add -A" or "git add --all"
- `git\s+commit\s+.*(-a|--all)\b` matches "git commit -a" or "git commit --all" with any other flags (e.g., "git commit -am 'msg'")
- `\b` ensures word boundary (won't match "-am" as just "-a", which is fine since -am still auto-stages)

## Verification

Run shellcheck to verify syntax:
```bash
shellcheck /home/clemux/dev/cc-plugins/safer-git/hooks/guard-git.sh
```

Test the change by loading the plugin and attempting blocked/allowed commands:

```bash
claude --plugin-dir ~/dev/cc-plugins/safer-git
```

Test cases:
- **Should block:**
  - `git add -A`
  - `git add --all`
  - `git commit -a`
  - `git commit --all`
  - `git commit -am "message"`
  - `git commit -a -m "message"`
- **Should allow:**
  - `git add .`
  - `git add file.txt`
  - `git add src/`
  - `git add -p` (interactive/patch add is safe)
  - `git commit -m "message"` (explicit staging required)
