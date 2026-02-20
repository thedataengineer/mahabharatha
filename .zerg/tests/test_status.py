"""Tests for MAHABHARATHA v2 Status Command."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestProgressBar:
    """Tests for progress bar rendering."""

    def test_progress_bar_empty(self):
        """Test progress bar at 0%."""
        from status import render_progress_bar

        bar = render_progress_bar(0, 10, width=20)
        assert "░" in bar or bar.count("█") == 0

    def test_progress_bar_full(self):
        """Test progress bar at 100%."""
        from status import render_progress_bar

        bar = render_progress_bar(10, 10, width=20)
        assert "█" in bar

    def test_progress_bar_half(self):
        """Test progress bar at 50%."""
        from status import render_progress_bar

        bar = render_progress_bar(5, 10, width=20)
        # Should have roughly half filled
        assert "█" in bar
        assert "░" in bar

    def test_progress_bar_percentage(self):
        """Test progress bar includes percentage."""
        from status import render_progress_bar

        bar = render_progress_bar(5, 10, width=20)
        assert "50" in bar and "%" in bar


class TestLevelStatus:
    """Tests for level status rendering."""

    def test_level_status_creation(self):
        """Test LevelStatus can be created."""
        from status import LevelStatus

        ls = LevelStatus(
            level=0,
            total_tasks=5,
            completed_tasks=3,
            is_current=True,
        )
        assert ls.level == 0
        assert ls.total_tasks == 5

    def test_level_status_percentage(self):
        """Test LevelStatus percentage calculation."""
        from status import LevelStatus

        ls = LevelStatus(level=0, total_tasks=10, completed_tasks=5, is_current=True)
        assert ls.percentage == 50.0

    def test_level_status_complete(self):
        """Test LevelStatus complete flag."""
        from status import LevelStatus

        complete = LevelStatus(
            level=0, total_tasks=5, completed_tasks=5, is_current=False
        )
        assert complete.is_complete is True

        incomplete = LevelStatus(
            level=0, total_tasks=5, completed_tasks=3, is_current=True
        )
        assert incomplete.is_complete is False


class TestWorkerStatus:
    """Tests for worker status rendering."""

    def test_worker_status_creation(self):
        """Test WorkerStatus can be created."""
        from status import WorkerStatus

        ws = WorkerStatus(
            worker_id="W1",
            state="EXECUTING",
            task_id="TASK-001",
            elapsed_seconds=120,
        )
        assert ws.worker_id == "W1"
        assert ws.state == "EXECUTING"

    def test_worker_status_idle(self):
        """Test WorkerStatus for idle worker."""
        from status import WorkerStatus

        ws = WorkerStatus(
            worker_id="W1",
            state="IDLE",
            task_id=None,
            elapsed_seconds=0,
        )
        assert ws.is_active is False

    def test_worker_status_active(self):
        """Test WorkerStatus for active worker."""
        from status import WorkerStatus

        ws = WorkerStatus(
            worker_id="W1",
            state="EXECUTING",
            task_id="TASK-001",
            elapsed_seconds=60,
        )
        assert ws.is_active is True


class TestQualityGateStatus:
    """Tests for quality gate status."""

    def test_quality_gate_status_creation(self):
        """Test QualityGateStatus can be created."""
        from status import QualityGateStatus

        qs = QualityGateStatus(
            name="lint",
            passed=True,
            message="All checks passed",
        )
        assert qs.name == "lint"
        assert qs.passed is True


class TestDashboard:
    """Tests for dashboard rendering."""

    def test_dashboard_creation(self):
        """Test Dashboard can be created."""
        from status import Dashboard

        db = Dashboard(
            feature_name="my-feature",
            current_level=1,
            total_levels=5,
            total_tasks=32,
            completed_tasks=8,
            levels=[],
            workers=[],
            quality_gates=[],
            elapsed_seconds=600,
        )
        assert db.feature_name == "my-feature"
        assert db.total_tasks == 32

    def test_dashboard_overall_percentage(self):
        """Test Dashboard overall percentage."""
        from status import Dashboard

        db = Dashboard(
            feature_name="test",
            current_level=1,
            total_levels=5,
            total_tasks=100,
            completed_tasks=25,
            levels=[],
            workers=[],
            quality_gates=[],
            elapsed_seconds=0,
        )
        assert db.overall_percentage == 25.0

    def test_dashboard_active_workers(self):
        """Test Dashboard active worker count."""
        from status import Dashboard, WorkerStatus

        workers = [
            WorkerStatus("W1", "EXECUTING", "T1", 60),
            WorkerStatus("W2", "IDLE", None, 0),
            WorkerStatus("W3", "VERIFYING", "T2", 30),
        ]
        db = Dashboard(
            feature_name="test",
            current_level=1,
            total_levels=5,
            total_tasks=10,
            completed_tasks=3,
            levels=[],
            workers=workers,
            quality_gates=[],
            elapsed_seconds=0,
        )
        assert db.active_workers == 2


class TestStatusCommand:
    """Tests for StatusCommand class."""

    def test_status_command_creation(self):
        """Test StatusCommand can be created."""
        from status import StatusCommand

        sc = StatusCommand()
        assert sc is not None

    def test_format_dashboard_has_header(self):
        """Test formatted dashboard has header."""
        from status import Dashboard, StatusCommand

        db = Dashboard(
            feature_name="my-feature",
            current_level=1,
            total_levels=5,
            total_tasks=32,
            completed_tasks=8,
            levels=[],
            workers=[],
            quality_gates=[],
            elapsed_seconds=600,
        )
        sc = StatusCommand()
        output = sc.format_dashboard(db)
        assert "MAHABHARATHA Status" in output
        assert "my-feature" in output

    def test_format_dashboard_has_progress(self):
        """Test formatted dashboard has progress info."""
        from status import Dashboard, LevelStatus, StatusCommand

        levels = [
            LevelStatus(0, 8, 8, is_current=False),
            LevelStatus(1, 10, 4, is_current=True),
        ]
        db = Dashboard(
            feature_name="test",
            current_level=1,
            total_levels=5,
            total_tasks=18,
            completed_tasks=12,
            levels=levels,
            workers=[],
            quality_gates=[],
            elapsed_seconds=0,
        )
        sc = StatusCommand()
        output = sc.format_dashboard(db)
        assert "Level" in output

    def test_format_dashboard_json_output(self):
        """Test dashboard JSON output."""
        from status import Dashboard, StatusCommand

        db = Dashboard(
            feature_name="test",
            current_level=1,
            total_levels=5,
            total_tasks=10,
            completed_tasks=3,
            levels=[],
            workers=[],
            quality_gates=[],
            elapsed_seconds=0,
        )
        sc = StatusCommand()
        output = sc.format_json(db)
        data = json.loads(output)
        assert data["feature_name"] == "test"
        assert data["total_tasks"] == 10


class TestTimeFormatting:
    """Tests for time formatting."""

    def test_format_duration_seconds(self):
        """Test formatting seconds."""
        from status import format_duration

        assert format_duration(45) == "45s"

    def test_format_duration_minutes(self):
        """Test formatting minutes."""
        from status import format_duration

        assert format_duration(125) == "2m 5s"

    def test_format_duration_hours(self):
        """Test formatting hours."""
        from status import format_duration

        assert format_duration(3725) == "1h 2m"
