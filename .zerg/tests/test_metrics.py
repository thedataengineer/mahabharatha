"""Tests for MAHABHARATHA v2 Metrics Collector."""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from metrics import LevelMetrics, MetricsCollector, TaskMetrics


class TestTaskMetrics:
    """Tests for TaskMetrics dataclass."""

    def test_task_metrics_creation(self):
        """Test TaskMetrics can be created."""
        from datetime import datetime

        tm = TaskMetrics(
            task_id="T1", worker_id="W1", started_at=datetime.now()
        )
        assert tm.task_id == "T1"
        assert tm.worker_id == "W1"
        assert tm.status == "running"

    def test_task_metrics_defaults(self):
        """Test TaskMetrics default values."""
        from datetime import datetime

        tm = TaskMetrics(task_id="T1", worker_id="W1", started_at=datetime.now())
        assert tm.completed_at is None
        assert tm.duration_seconds is None
        assert tm.context_usage == 0.0
        assert tm.token_count == 0


class TestLevelMetrics:
    """Tests for LevelMetrics dataclass."""

    def test_level_metrics_creation(self):
        """Test LevelMetrics can be created."""
        lm = LevelMetrics(level=0)
        assert lm.level == 0
        assert lm.tasks == []

    def test_level_duration_calculation(self):
        """Test level duration is calculated correctly."""
        from datetime import datetime, timedelta

        lm = LevelMetrics(level=0)
        lm.started_at = datetime.now()
        lm.completed_at = lm.started_at + timedelta(seconds=10)
        assert lm.duration_seconds == 10.0

    def test_level_duration_zero_when_incomplete(self):
        """Test level duration is zero when not complete."""
        lm = LevelMetrics(level=0)
        assert lm.duration_seconds == 0.0


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    def test_collector_initialization(self):
        """Test collector initializes correctly."""
        mc = MetricsCollector()
        assert mc.tasks == {}
        assert mc.levels == {}
        assert mc.execution_id is not None

    def test_record_task_start(self):
        """Test recording task start."""
        mc = MetricsCollector()
        mc.record_task_start("T1", "W1")
        assert "T1" in mc.tasks
        assert mc.tasks["T1"].worker_id == "W1"
        assert mc.tasks["T1"].status == "running"

    def test_record_task_end(self):
        """Test recording task end."""
        mc = MetricsCollector()
        mc.record_task_start("T1", "W1")
        mc.record_task_end("T1")
        assert mc.tasks["T1"].status == "complete"
        assert mc.tasks["T1"].completed_at is not None

    def test_record_task_end_with_status(self):
        """Test recording task end with status."""
        mc = MetricsCollector()
        mc.record_task_start("T1", "W1")
        mc.record_task_end("T1", status="failed")
        assert mc.tasks["T1"].status == "failed"

    def test_record_task_end_with_metrics(self):
        """Test recording task end with metrics."""
        mc = MetricsCollector()
        mc.record_task_start("T1", "W1")
        mc.record_task_end("T1", context_usage=0.5, token_count=1000)
        assert mc.tasks["T1"].context_usage == 0.5
        assert mc.tasks["T1"].token_count == 1000

    def test_record_task_end_nonexistent(self):
        """Test recording end for nonexistent task doesn't raise."""
        mc = MetricsCollector()
        mc.record_task_end("nonexistent")  # Should not raise

    def test_duration_tracking(self):
        """Test duration is tracked correctly."""
        mc = MetricsCollector()
        mc.record_task_start("T1", "W1")
        time.sleep(0.1)
        mc.record_task_end("T1")
        assert mc.tasks["T1"].duration_seconds >= 0.1


class TestLevelTracking:
    """Tests for level tracking."""

    def test_record_level_start(self):
        """Test recording level start."""
        mc = MetricsCollector()
        mc.record_level_start(0)
        assert 0 in mc.levels
        assert mc.levels[0].started_at is not None

    def test_record_level_end(self):
        """Test recording level end."""
        mc = MetricsCollector()
        mc.record_level_start(0)
        mc.record_level_end(0)
        assert mc.levels[0].completed_at is not None

    def test_record_level_end_nonexistent(self):
        """Test recording end for nonexistent level doesn't raise."""
        mc = MetricsCollector()
        mc.record_level_end(99)  # Should not raise


class TestSummary:
    """Tests for summary generation."""

    def test_get_summary_empty(self):
        """Test summary with no tasks."""
        mc = MetricsCollector()
        summary = mc.get_summary()
        assert summary["total_tasks"] == 0
        assert summary["completed_tasks"] == 0
        assert summary["failed_tasks"] == 0

    def test_get_summary_with_tasks(self):
        """Test summary with tasks."""
        mc = MetricsCollector()
        mc.record_task_start("T1", "W1")
        mc.record_task_end("T1", token_count=500)
        mc.record_task_start("T2", "W2")
        mc.record_task_end("T2", status="failed", token_count=500)

        summary = mc.get_summary()
        assert summary["total_tasks"] == 2
        assert summary["completed_tasks"] == 1
        assert summary["failed_tasks"] == 1
        assert summary["total_tokens"] == 1000

    def test_cost_estimation(self):
        """Test cost estimation."""
        mc = MetricsCollector()
        mc.record_task_start("T1", "W1")
        mc.record_task_end("T1", token_count=1_000_000)
        summary = mc.get_summary()
        # 1M tokens at $9/1M = $9
        assert summary["estimated_cost_usd"] == 9.0


class TestExport:
    """Tests for metrics export."""

    def test_export(self, tmp_path):
        """Test exporting metrics to JSON."""
        mc = MetricsCollector()
        mc.record_task_start("T1", "W1")
        mc.record_task_end("T1")
        path = mc.export(tmp_path / "metrics.json")
        assert path.exists()

    def test_export_content(self, tmp_path):
        """Test exported content is valid JSON."""
        mc = MetricsCollector()
        mc.record_task_start("T1", "W1")
        mc.record_task_end("T1", token_count=100)
        path = mc.export(tmp_path / "metrics.json")

        data = json.loads(path.read_text())
        assert "summary" in data
        assert "tasks" in data
        assert data["summary"]["total_tasks"] == 1

    def test_export_default_path(self, tmp_path, monkeypatch):
        """Test export to default path."""
        monkeypatch.setattr(MetricsCollector, "METRICS_DIR", tmp_path)
        mc = MetricsCollector()
        mc.record_task_start("T1", "W1")
        mc.record_task_end("T1")
        path = mc.export()
        assert path.exists()
        assert tmp_path in path.parents or path.parent == tmp_path
