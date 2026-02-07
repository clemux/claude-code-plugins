# Plan: Convert cc-plugins into a Claude Code plugin marketplace

## Decisions

- **Repo strategy:** Monorepo (fresh git init, remove individual `.git/` dirs)
- **Marketplace name:** `cc-plugins`
- **Owner:** Clément Schreiner
- **License:** MIT
- **Task runner:** mise (with `uv:commitizen` for tool install)
- **Pre-commit:** prek with commitizen hook + shellcheck
- **Version management:** Per-plugin `.cz.toml` with `version_files` pointing to `plugin.json`
- **GitHub:** User handles repo creation and push

## Tasks

### 1. Remove individual git repos

```bash
rm -rf safer-git/.git subagent-metrics/.git
```

### 2. Create `.claude-plugin/marketplace.json`

```json
{
  "name": "cc-plugins",
  "owner": {
    "name": "Clément Schreiner"
  },
  "metadata": {
    "description": "Safety and observability plugins for Claude Code"
  },
  "plugins": [
    {
      "name": "safer-git",
      "source": "./safer-git",
      "description": "Blocks dangerous git commands (force-push, amend, reset --hard, etc.) for all agents",
      "version": "1.1.0",
      "license": "MIT",
      "keywords": ["git", "safety", "hooks"],
      "category": "safety",
      "tags": ["PreToolUse", "guard"]
    },
    {
      "name": "subagent-metrics",
      "source": "./subagent-metrics",
      "description": "Logs token usage for every subagent (Task tool) call to ~/.claude/subagent-metrics.jsonl",
      "version": "1.0.0",
      "license": "MIT",
      "keywords": ["metrics", "tokens", "observability"],
      "category": "observability",
      "tags": ["PostToolUse", "logging"]
    }
  ]
}
```

### 3. Enrich `plugin.json` manifests

Add `version` and `license` to both.

**`safer-git/.claude-plugin/plugin.json`:**
```json
{
  "name": "safer-git",
  "description": "Blocks dangerous git commands (force-push, amend, reset --hard, etc.) for all agents",
  "version": "1.1.0",
  "license": "MIT"
}
```

**`subagent-metrics/.claude-plugin/plugin.json`:**
```json
{
  "name": "subagent-metrics",
  "description": "Logs token usage for every subagent (Task tool) call to ~/.claude/subagent-metrics.jsonl",
  "version": "1.0.0",
  "license": "MIT"
}
```

Version rationale: safer-git has 2 commits (initial + feature addition) → 1.1.0. subagent-metrics has 1 commit → 1.0.0.

### 4. Create per-plugin `.cz.toml` configs

Commitizen supports monorepo workflows via per-component configs. Each plugin gets independent version tracking and tagging.

**`safer-git/.cz.toml`:**
```toml
[tool.commitizen]
name = "cz_conventional_commits"
version = "1.1.0"
tag_format = "safer-git-v${version}"
update_changelog_on_bump = true
version_files = [
    ".claude-plugin/plugin.json:version"
]
```

**`subagent-metrics/.cz.toml`:**
```toml
[tool.commitizen]
name = "cz_conventional_commits"
version = "1.0.0"
tag_format = "subagent-metrics-v${version}"
update_changelog_on_bump = true
version_files = [
    ".claude-plugin/plugin.json:version"
]
```

Bump workflow:
```bash
mise run bump:safer-git
mise run bump:subagent-metrics
```

### 5. Create `mise.toml`

```toml
[tools]
"uv:commitizen" = "latest"

[tasks.lint]
description = "Run shellcheck on all hook scripts"
run = "shellcheck safer-git/hooks/guard-git.sh subagent-metrics/hooks/log-subagent-usage.sh"

[tasks.validate]
description = "Validate marketplace structure"
run = "claude plugin validate ."

[tasks."bump:safer-git"]
description = "Bump safer-git version"
run = "cz --config safer-git/.cz.toml bump --yes"

[tasks."bump:subagent-metrics"]
description = "Bump subagent-metrics version"
run = "cz --config subagent-metrics/.cz.toml bump --yes"
```

### 6. Create `.pre-commit-config.yaml` (for prek)

```yaml
repos:
  - repo: https://github.com/commitizen-tools/commitizen
    rev: v4.2.0
    hooks:
      - id: commitizen
  - repo: local
    hooks:
      - id: shellcheck
        name: shellcheck
        language: system
        entry: shellcheck
        files: '\.sh$'
```

### 7. Create `LICENSE`

MIT license, year 2026, Clément Schreiner.

### 8. Create `.gitignore`

```
*.lock
.claude/
*~
*.swp
.DS_Store
```

### 9. Create `.editorconfig`

```ini
root = true

[*]
end_of_line = lf
insert_final_newline = true
charset = utf-8

[*.sh]
indent_style = space
indent_size = 2

[*.json]
indent_style = space
indent_size = 2

[*.yaml]
indent_style = space
indent_size = 2

[*.toml]
indent_style = space
indent_size = 2

[*.md]
indent_style = space
indent_size = 2
trim_trailing_whitespace = false
```

### 10. Create root `README.md`

Brief marketplace README with installation instructions:
```
/plugin marketplace add <github-owner>/cc-plugins
/plugin install safer-git@cc-plugins
/plugin install subagent-metrics@cc-plugins
```

Plus brief descriptions of each plugin.

### 11. Update `CLAUDE.md`

Reflect the new marketplace structure:
- Remove references to "independent git repos"
- Add mise tasks (`mise run lint`, `mise run validate`)
- Add commitizen workflow (`cz commit`, per-plugin bump)
- Add prek setup (`prek install`)
- Document marketplace.json as the source of truth for plugin catalog

### 12. Init monorepo and initial commit

```bash
git init
git add -A
git commit -m "feat: init cc-plugins marketplace"
```

### 13. Install tooling and verify

```bash
mise install                    # installs commitizen via uv
prek install                    # installs git hooks
mise run lint                   # shellcheck passes
mise run validate               # marketplace validates (if claude CLI available)
```

## Files summary

| Action | File |
|--------|------|
| Delete | `safer-git/.git/` |
| Delete | `subagent-metrics/.git/` |
| Create | `.claude-plugin/marketplace.json` |
| Create | `safer-git/.cz.toml` |
| Create | `subagent-metrics/.cz.toml` |
| Create | `mise.toml` |
| Create | `.pre-commit-config.yaml` |
| Create | `LICENSE` |
| Create | `.gitignore` |
| Create | `.editorconfig` |
| Create | `README.md` |
| Modify | `safer-git/.claude-plugin/plugin.json` |
| Modify | `subagent-metrics/.claude-plugin/plugin.json` |
| Modify | `CLAUDE.md` |
| Git    | `git init` + initial commit |
