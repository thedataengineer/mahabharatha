"""MAHABHARATHA v2 Status Command - Dashboard rendering and progress tracking."""

import json
from dataclasses import dataclass


def render_progress_bar(completed: int, total: int, width: int = 20) -> str:
    """Render a text progress bar.

    Args:
        completed: Number of completed items
        total: Total number of items
        width: Width of the bar in characters

    Returns:
        Formatted progress bar string
    """
    percentage = 0 if total == 0 else (completed / total) * 100

    filled = int(width * completed / total) if total > 0 else 0
    empty = width - filled

    bar = "█" * filled + "░" * empty
    return f"[{bar}] {percentage:5.1f}%"


def format_duration(seconds: int) -> str:
    """Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


@dataclass
class LevelStatus:
    """Status of a single level."""

    level: int
    total_tasks: int
    completed_tasks: int
    is_current: bool

    @property
    def percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100

    @property
    def is_complete(self) -> bool:
        """Check if level is complete."""
        return self.completed_tasks >= self.total_tasks


@dataclass
class WorkerStatus:
    """Status of a single worker."""

    worker_id: str
    state: str
    task_id: str | None
    elapsed_seconds: int

    @property
    def is_active(self) -> bool:
        """Check if worker is actively working."""
        return self.state not in ("IDLE", "STOPPED")


@dataclass
class QualityGateStatus:
    """Status of a quality gate."""

    name: str
    passed: bool
    message: str = ""


@dataclass
class Dashboard:
    """Complete dashboard state."""

    feature_name: str
    current_level: int
    total_levels: int
    total_tasks: int
    completed_tasks: int
    levels: list[LevelStatus]
    workers: list[WorkerStatus]
    quality_gates: list[QualityGateStatus]
    elapsed_seconds: int
    estimated_remaining: int = 0

    @property
    def overall_percentage(self) -> float:
        """Calculate overall completion percentage."""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100

    @property
    def active_workers(self) -> int:
        """Count active workers."""
        return sum(1 for w in self.workers if w.is_active)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "feature_name": self.feature_name,
            "current_level": self.current_level,
            "total_levels": self.total_levels,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "overall_percentage": self.overall_percentage,
            "active_workers": self.active_workers,
            "total_workers": len(self.workers),
            "elapsed_seconds": self.elapsed_seconds,
            "estimated_remaining": self.estimated_remaining,
            "levels": [
                {
                    "level": lv.level,
                    "total_tasks": lv.total_tasks,
                    "completed_tasks": lv.completed_tasks,
                    "percentage": lv.percentage,
                    "is_complete": lv.is_complete,
                    "is_current": lv.is_current,
                }
                for lv in self.levels
            ],
            "workers": [
                {
                    "worker_id": w.worker_id,
                    "state": w.state,
                    "task_id": w.task_id,
                    "elapsed_seconds": w.elapsed_seconds,
                    "is_active": w.is_active,
                }
                for w in self.workers
            ],
            "quality_gates": [
                {
                    "name": qg.name,
                    "passed": qg.passed,
                    "message": qg.message,
                }
                for qg in self.quality_gates
            ],
        }


class StatusCommand:
    """Render execution status dashboard."""

    def __init__(self):
        """Initialize status command."""
        pass

    def format_dashboard(self, dashboard: Dashboard) -> str:
        """Format dashboard as text.

        Args:
            dashboard: Dashboard state

        Returns:
            Formatted text output
        """
        lines = []

        # Header
        lines.append(f"MAHABHARATHA Status - Project: {dashboard.feature_name}")
        lines.append("═" * 60)
        lines.append("")

        # Overall progress
        lines.append(
            f"Progress: Level {dashboard.current_level}/{dashboard.total_levels} | "
            f"Tasks: {dashboard.completed_tasks}/{dashboard.total_tasks} "
            f"({dashboard.overall_percentage:.1f}%) | "
            f"Workers: {dashboard.active_workers}/{len(dashboard.workers)} active"
        )
        lines.append("")

        # Level progress
        for level in dashboard.levels:
            bar = render_progress_bar(level.completed_tasks, level.total_tasks)
            status = "✓" if level.is_complete else ("◆" if level.is_current else "⏳")
            task_info = f"({level.completed_tasks}/{level.total_tasks} tasks)"
            lines.append(f"Level {level.level} {bar} {task_info} {status}")
        lines.append("")

        # Workers
        if dashboard.workers:
            lines.append("Workers:")
            for w in dashboard.workers:
                state_icon = "●" if w.is_active else "○"
                task_info = f" {w.task_id}" if w.task_id else ""
                elapsed = f"({format_duration(w.elapsed_seconds)})" if w.is_active else ""
                lines.append(f"  [{w.worker_id}] {state_icon} {w.state}{task_info} {elapsed}")
            lines.append("")

        # Quality gates
        if dashboard.quality_gates:
            gate_status = " | ".join(f"{qg.name} {'✓' if qg.passed else '✗'}" for qg in dashboard.quality_gates)
            lines.append(f"Quality Gates: {gate_status}")
            lines.append("")

        # Timing
        elapsed = format_duration(dashboard.elapsed_seconds)
        if dashboard.estimated_remaining > 0:
            remaining = format_duration(dashboard.estimated_remaining)
            lines.append(f"Elapsed: {elapsed} | Estimated: {remaining} remaining")
        else:
            lines.append(f"Elapsed: {elapsed}")

        return "\n".join(lines)

    def format_json(self, dashboard: Dashboard) -> str:
        """Format dashboard as JSON.

        Args:
            dashboard: Dashboard state

        Returns:
            JSON string
        """
        return json.dumps(dashboard.to_dict(), indent=2)
