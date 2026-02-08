# worktree

Skill for managing git worktrees using [git gtr](https://github.com/coderabbitai/git-worktree-runner). Creates worktrees, copies files, and guides the user to navigate or start AI sessions in them.

## Prerequisites

- [git gtr](https://github.com/coderabbitai/git-worktree-runner) installed and available in PATH

## Installation

```bash
claude --plugin-dir path/to/worktree
```

## Usage

Invoke via `/worktree` with a free-form description of what you want to do:

```
/worktree my-feature                        # Create a worktree
/worktree new my-feature --from-current     # Create from current branch
/worktree copy my-feature -- ".env*"        # Copy files to a worktree
/worktree list                              # List all worktrees
/worktree rm my-feature                     # Remove a worktree
/worktree go my-feature                     # Get navigation instructions
```

## License

MIT
