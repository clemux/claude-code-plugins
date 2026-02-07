# Plan: Move `/commit` skill into a plugin

## Context

The `/commit` skill currently lives at `~/.claude/skills/commit/SKILL.md` and dispatches `general-purpose` Haiku subagents. Same problems as the test-runner skill had before migration:

1. **No attribution in metrics** -- `subagent_type: "general-purpose"` is indistinguishable from other subagent calls
2. **Not distributable** -- user-local file, not shareable via the plugin marketplace

Moving it into a plugin with a custom `commit` subagent gives us `subagent_type: "commit"` in metrics and makes it installable from the monorepo.

## Plugin structure

```
commit/
├── .claude-plugin/plugin.json    # Manifest
├── .cz.toml                      # Commitizen versioning
├── agents/commit.md              # Custom haiku subagent (Bash only)
├── skills/commit/SKILL.md        # Full multi-phase workflow
├── CLAUDE.md                     # Dev notes
└── README.md                     # User docs
```

No `scripts/` or `hooks/` directories -- this plugin has neither.

## Architecture note

Unlike test-runner (thin skill, heavy subagent), commit is the opposite:
- **Skill** is heavy: analysis, splitting heuristics, commit planning, hook failure handling (Opus)
- **Subagent** is thin: just executes git commands and reports structured results (Haiku)

## Files to create

### 1. `commit/.claude-plugin/plugin.json`

Standard manifest following safer-git/subagent-metrics pattern.

```json
{
  "name": "commit",
  "description": "Smart conventional commits with automatic change analysis and splitting",
  "version": "0.1.0",
  "license": "MIT"
}
```

### 2. `commit/.cz.toml`

Following safer-git's `.cz.toml` pattern:

```toml
[tool.commitizen]
name = "cz_conventional_commits"
version = "0.1.0"
tag_format = "commit-v${version}"
update_changelog_on_bump = true
version_files = [
    ".claude-plugin/plugin.json:version"
]
```

### 3. `commit/agents/commit.md`

Thin haiku subagent. Encodes the response format contract in the system prompt so per-dispatch prompts in SKILL.md can be shorter.

- **Tools**: Bash only (no Read needed -- just git execution)
- **Model**: haiku
- **System prompt**: execute git commands, report in structured format (OK/HOOK_FAILED/ERROR for commits, PUSHED/PUSH_FAILED for push)

### 4. `commit/skills/commit/SKILL.md`

Adapted from `~/.claude/skills/commit/SKILL.md` with these changes:
1. `subagent_type: "general-purpose"` → `subagent_type: "commit"` (Phase 3 and Phase 5)
2. Response format instructions removed from per-dispatch prompts (now in agent system prompt)

The following improvements from the user-local SKILL.md also carry over:
3. Intent-based splitting heuristics (unit of work, same-file-different-intent) replacing file-type-based heuristics
4. Always-confirm behavior: commit plan is always presented for user confirmation before executing
5. `auto` argument in frontmatter to skip confirmation when desired

### 5. `commit/CLAUDE.md`

Dev notes covering structure, architecture (heavy skill / thin subagent), metrics integration, testing instructions.

### 6. `commit/README.md`

User docs: installation, usage (`/commit`, `/commit push`), what it does, safety rules, files table.

## Files to update

### 7. `.claude-plugin/marketplace.json` -- add plugin entry

```json
{
  "name": "commit",
  "source": "./commit",
  "description": "Smart conventional commits with automatic change analysis and splitting",
  "version": "0.1.0",
  "license": "MIT",
  "keywords": ["git", "commit", "conventional-commits"],
  "category": "workflow",
  "tags": ["skill", "subagent"]
}
```

### 8. `CLAUDE.md` -- add to Plugins listing

Add commit plugin description to the Plugins section.

## Implementation order

1. Create `commit/.claude-plugin/plugin.json`
2. Create `commit/.cz.toml`
3. Create `commit/agents/commit.md`
4. Create `commit/skills/commit/SKILL.md`
5. Create `commit/CLAUDE.md`
6. Create `commit/README.md`
7. Update `.claude-plugin/marketplace.json`
8. Update root `CLAUDE.md`

## Verification

```bash
claude --plugin-dir ~/dev/cc-plugins/commit
```

1. `/commit` is available as a slash command
2. Make a change, run `/commit` -- verify commit is created with conventional format
3. Check `~/.claude/subagent-metrics.jsonl` shows `"subagent_type": "commit"` (with subagent-metrics loaded)
4. Both plugins together:
   ```bash
   claude --plugin-dir ~/dev/cc-plugins/commit --plugin-dir ~/dev/cc-plugins/subagent-metrics
   ```

## Post-migration cleanup

After verifying: `rm -r ~/.claude/skills/commit/`