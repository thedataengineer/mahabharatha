"""MAHABHARATHA v2 Metrics Collector - Execution monitoring and cost tracking."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class TaskMetrics:
    """Metrics for a single task."""

    task_id: str
    worker_id: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    context_usage: float = 0.0
    token_count: int = 0
    status: str = "running"


@dataclass
class LevelMetrics:
    """Metrics for a level."""

    level: int
    tasks: list[TaskMetrics] = field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def duration_seconds(self) -> float:
        """Calculate level duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0


class MetricsCollector:
    """Collects and exports execution metrics."""

    METRICS_DIR = Path(".mahabharatha/metrics")

    def __init__(self):
        """Initialize metrics collector."""
        self.tasks: dict[str, TaskMetrics] = {}
        self.levels: dict[int, LevelMetrics] = {}
        self.execution_id: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.METRICS_DIR.mkdir(parents=True, exist_ok=True)

    def record_task_start(self, task_id: str, worker_id: str) -> None:
        """Record task start.

        Args:
            task_id: Task identifier
            worker_id: Worker identifier
        """
        self.tasks[task_id] = TaskMetrics(task_id=task_id, worker_id=worker_id, started_at=datetime.now())

    def record_task_end(
        self,
        task_id: str,
        status: str = "complete",
        context_usage: float = 0.0,
        token_count: int = 0,
    ) -> None:
        """Record task completion.

        Args:
            task_id: Task identifier
            status: Final task status
            context_usage: Context usage ratio (0.0-1.0)
            token_count: Total tokens used
        """
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        task.completed_at = datetime.now()
        task.duration_seconds = (task.completed_at - task.started_at).total_seconds()
        task.status = status
        task.context_usage = context_usage
        task.token_count = token_count

    def record_level_start(self, level: int) -> None:
        """Record level start.

        Args:
            level: Level number
        """
        self.levels[level] = LevelMetrics(level=level, started_at=datetime.now())

    def record_level_end(self, level: int) -> None:
        """Record level completion.

        Args:
            level: Level number
        """
        if level not in self.levels:
            return
        self.levels[level].completed_at = datetime.now()

    def get_summary(self) -> dict:
        """Get execution summary.

        Returns:
            Dictionary with summary statistics
        """
        total_duration = sum(t.duration_seconds or 0 for t in self.tasks.values())
        total_tokens = sum(t.token_count for t in self.tasks.values())

        return {
            "execution_id": self.execution_id,
            "total_tasks": len(self.tasks),
            "completed_tasks": sum(1 for t in self.tasks.values() if t.status == "complete"),
            "failed_tasks": sum(1 for t in self.tasks.values() if t.status == "failed"),
            "total_duration_seconds": total_duration,
            "total_tokens": total_tokens,
            "estimated_cost_usd": self._estimate_cost(total_tokens),
            "avg_task_duration": total_duration / len(self.tasks) if self.tasks else 0,
            "levels": len(self.levels),
        }

    def _estimate_cost(self, tokens: int) -> float:
        """Estimate API cost (rough calculation).

        Args:
            tokens: Total token count

        Returns:
            Estimated cost in USD
        """
        # Assumes Claude Sonnet pricing (~$3/1M input, $15/1M output)
        # Rough average: $9/1M tokens
        return (tokens / 1_000_000) * 9.0

    def export(self, path: Path | None = None) -> Path:
        """Export metrics to JSON.

        Args:
            path: Output path (defaults to METRICS_DIR/metrics_{id}.json)

        Returns:
            Path to exported file
        """
        path = path or self.METRICS_DIR / f"metrics_{self.execution_id}.json"

        data = {
            "summary": self.get_summary(),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "worker_id": t.worker_id,
                    "started_at": t.started_at.isoformat(),
                    "completed_at": (t.completed_at.isoformat() if t.completed_at else None),
                    "duration_seconds": t.duration_seconds,
                    "context_usage": t.context_usage,
                    "token_count": t.token_count,
                    "status": t.status,
                }
                for t in self.tasks.values()
            ],
            "levels": [
                {
                    "level": lv.level,
                    "started_at": lv.started_at.isoformat() if lv.started_at else None,
                    "completed_at": (lv.completed_at.isoformat() if lv.completed_at else None),
                    "duration_seconds": lv.duration_seconds,
                    "task_count": len(lv.tasks),
                }
                for lv in self.levels.values()
            ],
        }

        path.write_text(json.dumps(data, indent=2))
        return path
