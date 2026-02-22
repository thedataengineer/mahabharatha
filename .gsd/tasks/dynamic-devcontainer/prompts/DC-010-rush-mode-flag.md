# DC-010: Add --mode Flag to Kurukshetra Command

**Level**: 4 | **Critical Path**: No | **Estimate**: 15 min
**Dependencies**: DC-009

## Objective

Add `--mode subprocess|container|auto` option to `mahabharatha kurukshetra` command. Pass the mode to the orchestrator configuration.

## Files Owned

- `mahabharatha/commands/kurukshetra.py` (modify)

## Files to Read

- `mahabharatha/config.py` (WorkersConfig)

## Implementation

### 1. Add CLI Option

```python
@click.command()
@click.option("--workers", "-w", default=5, type=int, help="Number of workers to launch")
@click.option("--feature", "-f", help="Feature name (auto-detected if not provided)")
@click.option("--level", "-l", type=int, help="Start from specific level")
@click.option("--dry-run", is_flag=True, help="Show plan without executing")
@click.option("--resume", is_flag=True, help="Continue from previous run")
@click.option("--timeout", default=3600, type=int, help="Max execution time (seconds)")
@click.option("--task-graph", "-g", help="Path to task-graph.json")
@click.option(
    "--mode", "-m",
    type=click.Choice(["subprocess", "container", "auto"]),
    default="auto",
    help="Worker execution mode (default: auto-detect)",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def kurukshetra(
    ctx: click.Context,
    workers: int,
    feature: str | None,
    level: int | None,
    dry_run: bool,
    resume: bool,
    timeout: int,
    task_graph: str | None,
    mode: str,
    verbose: bool,
) -> None:
    """Launch parallel worker execution.

    Spawns workers, assigns tasks, and monitors progress until completion.

    Examples:

        mahabharatha kurukshetra --workers 5

        mahabharatha kurukshetra --feature user-auth --dry-run

        mahabharatha kurukshetra --mode container --workers 3

        mahabharatha kurukshetra --resume --workers 3
    """
```

### 2. Apply Mode to Config

```python
    try:
        # Load configuration
        config = MahabharathaConfig.load()

        # Override launcher type if mode specified
        if mode != "auto":
            config.workers.launcher_type = mode
            console.print(f"Mode: [cyan]{mode}[/cyan]")

        # ... rest of existing code ...
```

### 3. Show Mode in Summary

Update `show_summary()`:

```python
def show_summary(task_data: dict, workers: int, mode: str = "auto") -> None:
    """Show execution summary.

    Args:
        task_data: Task graph data
        workers: Worker count
        mode: Execution mode
    """
    tasks = task_data.get("tasks", [])
    levels = task_data.get("levels", {})

    table = Table(title="Execution Summary", show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value")

    table.add_row("Feature", task_data.get("feature", "unknown"))
    table.add_row("Total Tasks", str(len(tasks)))
    table.add_row("Levels", str(len(levels)))
    table.add_row("Workers", str(workers))
    table.add_row("Mode", mode)  # NEW
    table.add_row("Max Parallelization", str(task_data.get("max_parallelization", workers)))

    if "critical_path_minutes" in task_data:
        table.add_row("Critical Path", f"{task_data['critical_path_minutes']} min")

    console.print(table)
```

### 4. Update Call Sites

```python
        # Show summary
        show_summary(task_data, workers, mode)

        # ... in dry_run section ...
        if dry_run:
            show_dry_run(task_data, workers, feature, mode)
            return
```

### 5. Show Container Mode Availability in Dry Run

```python
def show_dry_run(task_data: dict, workers: int, feature: str, mode: str = "auto") -> None:
    """Show dry run plan."""
    console.print("\n[bold]Dry Run - Execution Plan[/bold]\n")

    # Show mode status
    if mode == "auto" or mode == "container":
        from mahabharatha.orchestrator import Orchestrator
        from mahabharatha.config import MahabharathaConfig
        orch = Orchestrator(feature, MahabharathaConfig())
        available, reason = orch.container_mode_available()
        if mode == "container" and not available:
            console.print(f"[yellow]Warning:[/yellow] Container mode requested but: {reason}")
        elif mode == "auto":
            effective = "container" if available else "subprocess"
            console.print(f"Auto-detected mode: [cyan]{effective}[/cyan] ({reason})")

    # ... rest of existing code ...
```

## Verification

```bash
# Check --mode appears in help
mahabharatha kurukshetra --help | grep -E '\-\-mode|\-m'

# Check mode options
mahabharatha kurukshetra --help | grep -E 'subprocess|container|auto'

# Test dry run with mode
mahabharatha kurukshetra --mode subprocess --dry-run 2>&1 | head -20
```

## Acceptance Criteria

- [ ] --mode/-m option accepts subprocess, container, auto
- [ ] Default is "auto"
- [ ] Mode is passed to config.workers.launcher_type
- [ ] Summary table shows mode
- [ ] Dry run shows container mode availability
- [ ] Help text documents the option
- [ ] No ruff errors: `ruff check mahabharatha/commands/kurukshetra.py`
