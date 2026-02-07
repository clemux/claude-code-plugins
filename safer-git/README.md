# safer-git

A Claude Code plugin that blocks dangerous git commands for all agents (main + subagents).

## Installation

```bash
claude --plugin-dir ~/dev/cc-plugins/safer-git
```

## What it blocks

### Remote history rewrite
| Command pattern | Description |
|----------------|-------------|
| `git push --force` / `-f` | Force push (rewrites remote history) |
| `git push --force-with-lease` | Still rewrites remote history; blocks the common agent bypass |
| `git push --delete` | Delete remote branch |
| `git push origin :branch` | Delete remote branch (colon-refspec syntax) |

### Commit / hook bypass
| Command pattern | Description |
|----------------|-------------|
| `git commit --amend` | Amend commit (rewrites history) |
| `git commit --no-verify` / `-n` | Skip pre-commit hooks |

### Discard uncommitted work
| Command pattern | Description |
|----------------|-------------|
| `git reset --hard` | Hard reset (discards uncommitted changes) |
| `git checkout .` | Discard all working tree changes |
| `git restore .` | Discard all working tree changes |
| `git clean -f` | Delete untracked files |

### Branch destruction
| Command pattern | Description |
|----------------|-------------|
| `git branch -D` | Force-delete branch |

### History rewrite tools
| Command pattern | Description |
|----------------|-------------|
| `git rebase -i` / `--interactive` | Interactive rebase |
| `git filter-branch` | Full history rewrite |

### Irrecoverable data loss
| Command pattern | Description |
|----------------|-------------|
| `git stash drop` | Permanently deletes a stash entry |
| `git stash clear` | Permanently deletes all stashes |
| `git reflog expire` | Removes the reflog (recovery safety net) |
| `git gc --prune` | Makes unreachable objects unrecoverable |

### Bypass prevention
| Command pattern | Description |
|----------------|-------------|
| `git config alias.*` | Blocks alias creation (prevents `alias.yolo = push --force` bypass) |

## How it works

The plugin registers a PreToolUse hook on the Bash tool. When any agent (including subagents like Haiku) attempts to run a Bash command:

1. The hook extracts the command string from the tool input
2. Splits compound commands (`&&`, `||`, `;`, `|`) into segments
3. Checks each segment against the blocked pattern list using regex
4. If a dangerous pattern is found: denies execution with a descriptive message
5. If safe: allows execution silently

## Dependencies

- `jq` — for parsing hook input JSON
- `grep -P` (PCRE) — for regex matching

## Agent bypass vectors and mitigations

| Vector | Mitigated? | Notes |
|--------|-----------|-------|
| Suggest alternative flag (`--force-with-lease`) | Yes | Blocked explicitly |
| Create git alias (`git config alias.yolo "push --force"`) | Yes | `git config alias.*` is blocked |
| Use colon-refspec (`git push origin :branch`) | Yes | Blocked explicitly |
| Write dangerous command to a script file, then `bash script.sh` | No | Hook only sees `bash script.sh`, not file contents |
| Use `eval "git push --force"` | No | Hook sees the eval string but regex may not parse it reliably |
| Python/node subprocess (`subprocess.run(["git", "push", "--force"])`) | No | Entirely outside Bash tool |
| Subshells: `$(git push --force)` inside a larger command | Partial | Depends on command splitting |

### Remaining known limitations

- **Pre-existing aliases**: If aliases were set up before the plugin was loaded, `git <alias>` will bypass detection since the alias is resolved by git, not the shell command string.
- **Script execution**: If a dangerous command is written to a file via the Write tool and then executed (e.g., `bash script.sh`), the hook cannot inspect the file contents.
- **Eval / indirect execution**: `eval`, `xargs`, or piping to `bash`/`sh` can obscure the actual command.
- **Non-Bash tools**: Commands run via Python, Node, or other runtimes bypass the Bash tool hook entirely.
