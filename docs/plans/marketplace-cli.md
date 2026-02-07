# Plan: `marketplace.py` CLI Script

## Context

Maintaining `marketplace.json` manually is error-prone — fields drift from individual `plugin.json` files, and adding a new plugin requires remembering the exact schema. A small CLI tool automates these operations.

The script will be a single-file PEP 723 script runnable via `uv run`, using Typer for the CLI framework.

## File to create

**`scripts/marketplace.py`** — single file, no package structure.

### PEP 723 header

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["typer[all]>=0.15"]
# ///
```

`typer[all]` includes `rich` for table output. Everything else is stdlib (`json`, `pathlib`).

## Commands

### Global option

`--marketplace / -m` — explicit path to `marketplace.json`. Auto-discovered by default by walking up from the script's location looking for `.claude-plugin/marketplace.json`. Passed to commands via `typer.Context.obj`.

### `list`

```
uv run scripts/marketplace.py list
```

Prints a Rich table: name, version, category, description (truncated). No arguments.

### `add PLUGIN_NAME`

```
uv run scripts/marketplace.py add test-runner --keywords testing,pytest --category testing --tags skill
```

1. Validate `<name>/.claude-plugin/plugin.json` exists
2. Check plugin not already in marketplace
3. Read `name`, `description`, `version`, `license` from plugin.json
4. Accept `--source` (default `"./<name>"`), `--keywords`, `--category`, `--tags` as options; prompt interactively via `typer.prompt()` if omitted
5. Append to `plugins[]`, write marketplace.json

`PLUGIN_NAME` is required (no auto-discover mode).

### `update-version PLUGIN_NAME`

```
uv run scripts/marketplace.py update-version safer-git
uv run scripts/marketplace.py update-version safer-git --version 2.0.0
```

1. Find plugin in marketplace by name
2. Read new version from `--version` flag or from plugin.json
3. Update and write if changed

### `sync`

```
uv run scripts/marketplace.py sync [--dry-run]
```

For each plugin in marketplace.json, read its plugin.json and update shared fields (`version`, `description`, `license`). `--dry-run` prints diffs without writing.

## Key helpers

| Function | Purpose |
|---|---|
| `find_repo_root(start)` | Walk up from `start` to find dir containing `.claude-plugin/marketplace.json` |
| `load_marketplace(path)` / `save_marketplace(path, data)` | Read/write with 2-space indent + trailing newline (per `.editorconfig`) |
| `load_plugin_json(plugin_dir)` | Read `<dir>/.claude-plugin/plugin.json` |
| `find_plugin_entry(marketplace, name)` | Lookup by name, return `(index, entry)` or `None` |

## JSON formatting

Match `.editorconfig`: `json.dump(data, f, indent=2, ensure_ascii=False)` + `f.write("\n")`.

## Edge cases

- `add` rejects plugins already in marketplace (suggest `sync` instead)
- `sync` warns and skips if a source directory is missing
- Empty `--keywords`/`--tags` → store as `[]`, not `[""]`
- Source paths stored as `"./<dirname>"` (matching existing convention)

## Integration with existing tooling

Add to `mise.toml`:

```toml
[tasks."marketplace:list"]
description = "List marketplace plugins"
run = "uv run scripts/marketplace.py list"

[tasks."marketplace:sync"]
description = "Sync marketplace.json from plugin.json files"
run = "uv run scripts/marketplace.py sync"
```

## Verification

1. `uv run scripts/marketplace.py list` — shows safer-git and subagent-metrics
2. `uv run scripts/marketplace.py add test-runner --keywords testing,pytest --category testing --tags skill` — adds test-runner to marketplace.json
3. `uv run scripts/marketplace.py sync --dry-run` — reports no changes (or expected diffs)
4. `uv run scripts/marketplace.py update-version safer-git --version 2.0.0` — updates version, then revert
5. Verify the script runs cleanly with `uv run`
