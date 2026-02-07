# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer",
#     "rich",
# ]
# ///
"""CLI explorer for subagent-metrics JSONL logs."""

import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

DEFAULT_METRICS_PATH = Path.home() / ".claude" / "subagent-metrics.jsonl"

app = typer.Typer(help="Explore subagent-metrics logs.")
console = Console()

metrics_file: Path = DEFAULT_METRICS_PATH


def set_file(path: Optional[Path] = None) -> None:
    global metrics_file
    if path is not None:
        metrics_file = path


@app.callback()
def main(
    file: Annotated[
        Optional[Path],
        typer.Option("--file", "-f", help="Path to JSONL metrics file."),
    ] = None,
) -> None:
    set_file(file)


def load_entries() -> list[dict]:
    if not metrics_file.exists():
        console.print(f"[dim]No metrics file found at {metrics_file}[/dim]")
        raise typer.Exit(0)
    lines = metrics_file.read_text().strip().splitlines()
    if not lines:
        console.print("[dim]Metrics file is empty.[/dim]")
        raise typer.Exit(0)
    entries = []
    for line in lines:
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def truncate(s: str | None, n: int) -> str:
    if not s:
        return ""
    return s[:n] + "…" if len(s) > n else s


def fmt_tokens(t: int | None) -> str:
    return f"{t:,}" if t is not None else "—"


def fmt_duration(ms: int | None) -> str:
    if ms is None:
        return "—"
    if ms < 1000:
        return f"{ms}ms"
    return f"{ms / 1000:.1f}s"


@app.command()
def log(
    last: Annotated[int, typer.Option("--last", "-n", help="Number of entries.")] = 20,
    model: Annotated[Optional[str], typer.Option(help="Filter by model.")] = None,
    type: Annotated[
        Optional[str], typer.Option("--type", help="Filter by subagent type.")
    ] = None,
    skill: Annotated[Optional[str], typer.Option(help="Filter by skill.")] = None,
    session: Annotated[
        Optional[str], typer.Option(help="Filter by session (prefix match).")
    ] = None,
    cwd: Annotated[Optional[str], typer.Option(help="Filter by project path (prefix match).")] = None,
) -> None:
    """Show recent log entries as a table."""
    entries = load_entries()

    if model:
        entries = [e for e in entries if e.get("model") == model]
    if type:
        entries = [e for e in entries if e.get("subagent_type") == type]
    if skill:
        entries = [e for e in entries if e.get("skill") == skill]
    if session:
        entries = [e for e in entries if (e.get("session") or "").startswith(session)]
    if cwd:
        entries = [e for e in entries if (e.get("cwd") or "").startswith(cwd)]

    entries = entries[-last:]

    if not entries:
        console.print("[dim]No matching entries.[/dim]")
        raise typer.Exit(0)

    table = Table(title="Subagent Metrics Log", show_lines=False)
    table.add_column("Timestamp", style="dim")
    table.add_column("Session")
    table.add_column("Project", style="blue")
    table.add_column("Model", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Skill", style="magenta")
    table.add_column("Description")
    table.add_column("Tokens", justify="right")
    table.add_column("Duration", justify="right")

    for e in entries:
        table.add_row(
            e.get("ts", ""),
            truncate(e.get("session"), 8),
            truncate(e.get("cwd"), 30),
            e.get("model", ""),
            e.get("subagent_type", ""),
            e.get("skill") or "—",
            truncate(e.get("description"), 40),
            fmt_tokens(e.get("total_tokens")),
            fmt_duration(e.get("duration_ms")),
        )

    console.print(table)


@app.command()
def summary(
    by: Annotated[
        str, typer.Option("--by", help="Group by: model, type, or skill.")
    ] = "model",
    session: Annotated[
        Optional[str], typer.Option(help="Filter by session (prefix match).")
    ] = None,
) -> None:
    """Show aggregate stats grouped by a dimension."""
    field_map = {"model": "model", "type": "subagent_type", "skill": "skill"}
    if by not in field_map:
        console.print(f"[red]Invalid --by value: {by}. Choose model, type, or skill.[/red]")
        raise typer.Exit(1)

    field = field_map[by]
    entries = load_entries()

    if session:
        entries = [e for e in entries if (e.get("session") or "").startswith(session)]

    if not entries:
        console.print("[dim]No matching entries.[/dim]")
        raise typer.Exit(0)

    groups: dict[str, list[dict]] = {}
    for e in entries:
        key = e.get(field) or "(none)"
        groups.setdefault(key, []).append(e)

    table = Table(title=f"Summary by {by}")
    table.add_column(by.capitalize(), style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Total Tokens", justify="right")
    table.add_column("Avg Tokens", justify="right")
    table.add_column("Total Duration", justify="right")

    for key in sorted(groups):
        items = groups[key]
        count = len(items)
        tokens = [e["total_tokens"] for e in items if e.get("total_tokens") is not None]
        durations = [e["duration_ms"] for e in items if e.get("duration_ms") is not None]
        total_tok = sum(tokens) if tokens else None
        avg_tok = round(total_tok / len(tokens)) if tokens else None
        total_dur = sum(durations) if durations else None

        table.add_row(
            key,
            str(count),
            fmt_tokens(total_tok),
            fmt_tokens(avg_tok),
            fmt_duration(total_dur),
        )

    console.print(table)


@app.command()
def sessions(
    last: Annotated[
        int, typer.Option("--last", "-n", help="Number of recent sessions.")
    ] = 10,
) -> None:
    """List unique sessions."""
    entries = load_entries()

    session_data: dict[str, list[dict]] = {}
    for e in entries:
        sid = e.get("session") or "(unknown)"
        session_data.setdefault(sid, []).append(e)

    # Sort sessions by last seen timestamp, most recent last
    sorted_sessions = sorted(
        session_data.items(), key=lambda kv: kv[1][-1].get("ts", "")
    )
    sorted_sessions = sorted_sessions[-last:]

    table = Table(title="Sessions")
    table.add_column("Session", style="cyan")
    table.add_column("Project", style="blue")
    table.add_column("First Seen", style="dim")
    table.add_column("Last Seen", style="dim")
    table.add_column("Entries", justify="right")
    table.add_column("Models")
    table.add_column("Total Tokens", justify="right")

    for sid, items in sorted_sessions:
        timestamps = [e.get("ts", "") for e in items]
        cwds = sorted({e.get("cwd") or "?" for e in items})
        models = sorted({e.get("model", "?") for e in items})
        tokens = [e["total_tokens"] for e in items if e.get("total_tokens") is not None]
        total_tok = sum(tokens) if tokens else None

        table.add_row(
            truncate(sid, 8),
            truncate(", ".join(cwds), 30),
            min(timestamps) if timestamps else "",
            max(timestamps) if timestamps else "",
            str(len(items)),
            ", ".join(models),
            fmt_tokens(total_tok),
        )

    console.print(table)


if __name__ == "__main__":
    app()
