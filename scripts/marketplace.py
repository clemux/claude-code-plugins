#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["typer[all]>=0.15"]
# ///

"""Marketplace CLI for managing Claude Code plugins."""

import json
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="CLI for managing the Claude Code plugin marketplace")
console = Console()


def find_repo_root(start: Path) -> Optional[Path]:
    """
    Walk up from start directory to find the repo root containing .claude-plugin/marketplace.json.

    Args:
        start: Starting directory path

    Returns:
        Path to repo root if found, None otherwise
    """
    current = start.resolve()

    while current != current.parent:
        marketplace_path = current / ".claude-plugin" / "marketplace.json"
        if marketplace_path.exists():
            return current
        current = current.parent

    return None


def load_marketplace(path: Path) -> dict:
    """
    Load marketplace.json with error handling.

    Args:
        path: Path to marketplace.json file

    Returns:
        Parsed JSON data as dictionary
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        console.print(f"[red]Error: marketplace.json not found at {path}[/red]")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in {path}: {e}[/red]")
        raise typer.Exit(1)


def save_marketplace(path: Path, data: dict) -> None:
    """
    Save marketplace.json with consistent formatting (2-space indent + trailing newline).

    Args:
        path: Path to marketplace.json file
        data: Dictionary to serialize
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        console.print(f"[red]Error: Failed to write {path}: {e}[/red]")
        raise typer.Exit(1)


def load_plugin_json(plugin_dir: Path) -> dict:
    """
    Load plugin.json from a plugin directory.

    Args:
        plugin_dir: Path to plugin directory

    Returns:
        Parsed plugin.json data
    """
    plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
    try:
        with open(plugin_json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        console.print(f"[red]Error: plugin.json not found at {plugin_json_path}[/red]")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in {plugin_json_path}: {e}[/red]")
        raise typer.Exit(1)


def find_plugin_entry(marketplace: dict, name: str) -> Optional[tuple[int, dict]]:
    """
    Find a plugin entry in the marketplace by name.

    Args:
        marketplace: Marketplace data dictionary
        name: Plugin name to search for

    Returns:
        Tuple of (index, entry) if found, None otherwise
    """
    plugins = marketplace.get("plugins", [])
    for idx, entry in enumerate(plugins):
        if entry.get("name") == name:
            return (idx, entry)
    return None


@app.callback()
def main(
    ctx: typer.Context,
    marketplace: Annotated[
        Optional[Path],
        typer.Option(
            "--marketplace",
            "-m",
            help="Path to marketplace.json (auto-discovered by default)",
        ),
    ] = None,
):
    """Marketplace CLI for managing Claude Code plugins."""
    if marketplace is None:
        # Auto-discover marketplace.json by walking up from script location
        script_dir = Path(__file__).parent
        repo_root = find_repo_root(script_dir)

        if repo_root is None:
            console.print(
                "[red]Error: Could not find .claude-plugin/marketplace.json. "
                "Use --marketplace to specify the path explicitly.[/red]"
            )
            raise typer.Exit(1)

        marketplace = repo_root / ".claude-plugin" / "marketplace.json"

    # Store marketplace path in context for commands to access
    ctx.obj = {"marketplace_path": marketplace}


@app.command()
def list(ctx: typer.Context):
    """List all plugins in the marketplace."""
    marketplace_path = ctx.obj["marketplace_path"]
    marketplace_data = load_marketplace(marketplace_path)

    plugins = marketplace_data.get("plugins", [])

    if not plugins:
        console.print("[yellow]No plugins found in marketplace.[/yellow]")
        return

    # Create Rich table
    table = Table(title="Plugin Marketplace")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Version", style="magenta")
    table.add_column("Category", style="green")
    table.add_column("Description", style="white")

    for plugin in plugins:
        name = plugin.get("name", "")
        version = plugin.get("version", "")
        category = plugin.get("category", "")
        description = plugin.get("description", "")

        # Truncate description to ~60 chars
        if len(description) > 60:
            description = description[:57] + "..."

        table.add_row(name, version, category, description)

    console.print(table)


@app.command()
def add(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Plugin name (directory name)")],
    source: Annotated[
        Optional[str], typer.Option("--source", "-s", help="Source path")
    ] = None,
    keywords: Annotated[
        Optional[str], typer.Option("--keywords", "-k", help="Comma-separated keywords")
    ] = None,
    category: Annotated[
        Optional[str], typer.Option("--category", "-c", help="Plugin category")
    ] = None,
    tags: Annotated[
        Optional[str], typer.Option("--tags", "-t", help="Comma-separated tags")
    ] = None,
):
    """Add a new plugin to the marketplace."""
    marketplace_path = ctx.obj["marketplace_path"]
    repo_root = marketplace_path.parent.parent

    # 1. Validate plugin.json exists
    plugin_dir = repo_root / name
    if not plugin_dir.exists():
        console.print(f"[red]Error: Plugin directory not found: {plugin_dir}[/red]")
        raise typer.Exit(1)

    plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
    if not plugin_json_path.exists():
        console.print(f"[red]Error: plugin.json not found at {plugin_json_path}[/red]")
        raise typer.Exit(1)

    # 2. Load marketplace and check if plugin already exists
    marketplace_data = load_marketplace(marketplace_path)
    existing = find_plugin_entry(marketplace_data, name)

    if existing is not None:
        console.print(
            f"[red]Error: Plugin '{name}' already exists in marketplace. "
            f"Use 'sync' command instead to update it.[/red]"
        )
        raise typer.Exit(1)

    # 3. Read plugin.json
    plugin_data = load_plugin_json(plugin_dir)

    # Extract required fields
    plugin_name = plugin_data.get("name")
    plugin_description = plugin_data.get("description")
    plugin_version = plugin_data.get("version")
    plugin_license = plugin_data.get("license")

    if not plugin_name:
        console.print(f"[red]Error: 'name' field missing in {plugin_json_path}[/red]")
        raise typer.Exit(1)

    if plugin_name != name:
        console.print(
            f"[yellow]Warning: Directory name '{name}' does not match "
            f"plugin.json name '{plugin_name}'. Using plugin.json name.[/yellow]"
        )

    if not plugin_description:
        console.print(f"[red]Error: 'description' field missing in {plugin_json_path}[/red]")
        raise typer.Exit(1)

    if not plugin_version:
        console.print(f"[red]Error: 'version' field missing in {plugin_json_path}[/red]")
        raise typer.Exit(1)

    # 4. Set defaults and prompt for missing required fields
    if source is None:
        source = f"./{name}"

    if category is None:
        category = typer.prompt("Category")

    # 5. Parse comma-separated fields (handle empty strings)
    keywords_list = []
    if keywords:
        keywords_list = [k.strip() for k in keywords.split(",") if k.strip()]

    tags_list = []
    if tags:
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]

    # 6. Build new plugin entry
    new_entry = {
        "name": plugin_name,
        "description": plugin_description,
        "version": plugin_version,
        "source": source,
        "category": category,
    }

    if keywords_list:
        new_entry["keywords"] = keywords_list

    if tags_list:
        new_entry["tags"] = tags_list

    if plugin_license:
        new_entry["license"] = plugin_license

    # 7. Append to marketplace and save
    if "plugins" not in marketplace_data:
        marketplace_data["plugins"] = []

    marketplace_data["plugins"].append(new_entry)
    save_marketplace(marketplace_path, marketplace_data)

    console.print(f"[green]Successfully added plugin '{plugin_name}' to marketplace.[/green]")


@app.command(name="update-version")
def update_version(
    ctx: typer.Context,
    plugin_name: Annotated[str, typer.Argument(help="Plugin name to update")],
    version: Annotated[
        Optional[str],
        typer.Option("--version", "-v", help="New version (read from plugin.json if not provided)"),
    ] = None,
):
    """Update the version of a plugin in the marketplace."""
    marketplace_path = ctx.obj["marketplace_path"]
    repo_root = marketplace_path.parent.parent

    # 1. Find plugin in marketplace
    marketplace_data = load_marketplace(marketplace_path)
    plugin_entry = find_plugin_entry(marketplace_data, plugin_name)

    if plugin_entry is None:
        console.print(f"[red]Error: Plugin '{plugin_name}' not found in marketplace.[/red]")
        raise typer.Exit(1)

    idx, entry = plugin_entry

    # 2. Determine new version
    if version is None:
        # Read version from plugin.json
        plugin_dir = repo_root / plugin_name
        if not plugin_dir.exists():
            console.print(f"[red]Error: Plugin directory not found: {plugin_dir}[/red]")
            raise typer.Exit(1)

        plugin_data = load_plugin_json(plugin_dir)
        new_version = plugin_data.get("version")

        if not new_version:
            console.print(
                f"[red]Error: 'version' field missing in {plugin_dir}/.claude-plugin/plugin.json[/red]"
            )
            raise typer.Exit(1)
    else:
        new_version = version

    # 3. Check if version changed
    current_version = entry.get("version")

    if current_version == new_version:
        console.print(
            f"[yellow]Plugin '{plugin_name}' is already at version {new_version}. No changes made.[/yellow]"
        )
        return

    # 4. Update version and save
    marketplace_data["plugins"][idx]["version"] = new_version
    save_marketplace(marketplace_path, marketplace_data)

    console.print(
        f"[green]Successfully updated plugin '{plugin_name}' from version {current_version} to {new_version}.[/green]"
    )


@app.command()
def sync(
    ctx: typer.Context,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show differences without writing changes"),
    ] = False,
):
    """Sync marketplace entries with plugin.json files from each plugin directory."""
    marketplace_path = ctx.obj["marketplace_path"]
    repo_root = marketplace_path.parent.parent
    marketplace_data = load_marketplace(marketplace_path)

    plugins = marketplace_data.get("plugins", [])
    if not plugins:
        console.print("[yellow]No plugins found in marketplace.[/yellow]")
        return

    updated_count = 0
    skipped_count = 0
    missing_count = 0

    for idx, entry in enumerate(plugins):
        plugin_name = entry.get("name", "")
        source = entry.get("source", "")

        # Derive plugin directory from source field
        if not source:
            console.print(
                f"[yellow]Warning: Plugin '{plugin_name}' has no source field, skipping.[/yellow]"
            )
            skipped_count += 1
            continue

        # Remove leading "./" if present
        source_path = source.lstrip("./")
        plugin_dir = repo_root / source_path

        # Check if plugin directory exists
        if not plugin_dir.exists():
            console.print(
                f"[yellow]Warning: Plugin directory not found for '{plugin_name}' at {plugin_dir}, skipping.[/yellow]"
            )
            missing_count += 1
            continue

        # Load plugin.json
        try:
            plugin_data = load_plugin_json(plugin_dir)
        except typer.Exit:
            console.print(
                f"[yellow]Warning: Could not load plugin.json for '{plugin_name}', skipping.[/yellow]"
            )
            skipped_count += 1
            continue

        # Compare shared fields
        fields_to_sync = ["version", "description", "license"]
        differences = {}

        for field in fields_to_sync:
            marketplace_value = entry.get(field)
            plugin_value = plugin_data.get(field)

            # Only track actual differences (consider missing vs None as different)
            if marketplace_value != plugin_value:
                differences[field] = {
                    "marketplace": marketplace_value,
                    "plugin": plugin_value,
                }

        # If there are differences, update or report
        if differences:
            console.print(f"\n[cyan]Plugin: {plugin_name}[/cyan]")
            for field, values in differences.items():
                console.print(f"  [yellow]{field}:[/yellow]")
                console.print(f"    marketplace: {values['marketplace']}")
                console.print(f"    plugin.json: {values['plugin']}")

            if not dry_run:
                # Update the marketplace entry
                for field in differences:
                    plugin_value = plugin_data.get(field)
                    if plugin_value is not None:
                        marketplace_data["plugins"][idx][field] = plugin_value
                    elif field in marketplace_data["plugins"][idx]:
                        # Remove field from marketplace if it's missing in plugin.json
                        del marketplace_data["plugins"][idx][field]

            updated_count += 1

    # Save changes if not dry run
    if not dry_run and updated_count > 0:
        save_marketplace(marketplace_path, marketplace_data)
        console.print("\n[green]Marketplace updated successfully.[/green]")

    # Print summary
    console.print("\n[bold]Summary:[/bold]")
    if dry_run:
        console.print(f"  Plugins with differences: {updated_count}")
    else:
        console.print(f"  Plugins updated: {updated_count}")
    console.print(f"  Plugins skipped (errors): {skipped_count}")
    console.print(f"  Plugins skipped (missing): {missing_count}")
    console.print(f"  Total plugins checked: {len(plugins)}")


if __name__ == "__main__":
    app()