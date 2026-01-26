"""Tests for ZERG v2 Rush Command."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_execution_result_creation(self):
        """Test ExecutionResult can be created."""
        from rush import ExecutionResult

        result = ExecutionResult(
            validated=True,
            execution_id="test-001",
            tasks_completed=5,
            tasks_failed=0,
        )
        assert result.validated is True
        assert result.execution_id == "test-001"
        assert result.tasks_completed == 5

    def test_execution_result_defaults(self):
        """Test ExecutionResult default values."""
        from rush import ExecutionResult

        result = ExecutionResult(validated=True)
        assert result.execution_id is None
        assert result.tasks_completed == 0
        assert result.tasks_failed == 0
        assert result.errors == []


class TestRushCommandInit:
    """Tests for RushCommand initialization."""

    def test_rush_command_creation(self):
        """Test RushCommand can be created."""
        from rush import RushCommand

        rc = RushCommand()
        assert rc is not None

    def test_rush_command_has_orchestrator(self):
        """Test RushCommand has orchestrator reference."""
        from rush import RushCommand

        rc = RushCommand()
        assert hasattr(rc, "orchestrator")


class TestDryRun:
    """Tests for dry run mode."""

    def test_dry_run_validates_graph(self, tmp_path):
        """Test dry run validates task graph."""
        from rush import RushCommand

        # Create a valid task graph
        graph_data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "Test task",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": ["test.py"], "modify": [], "read": []},
                    "acceptance_criteria": ["Test passes"],
                    "verification": {"command": "echo ok", "timeout_seconds": 60},
                }
            ]
        }
        graph_file = tmp_path / "task-graph.json"
        graph_file.write_text(json.dumps(graph_data))

        rc = RushCommand()
        result = rc.execute(
            graph_path=graph_file,
            dry_run=True,
        )

        assert result.validated is True

    def test_dry_run_reports_validation_errors(self, tmp_path):
        """Test dry run reports validation errors (circular dependency detected at load)."""
        from rush import RushCommand

        # Create an invalid task graph (circular dependency)
        # Cycles are detected during graph loading and result in GraphLoadError
        graph_data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "Test 1",
                    "level": 0,
                    "dependencies": ["TASK-002"],
                    "files": {"create": ["a.py"], "modify": [], "read": []},
                    "acceptance_criteria": ["Test passes"],
                    "verification": {"command": "echo ok", "timeout_seconds": 60},
                },
                {
                    "id": "TASK-002",
                    "title": "Test 2",
                    "level": 0,
                    "dependencies": ["TASK-001"],
                    "files": {"create": ["b.py"], "modify": [], "read": []},
                    "acceptance_criteria": ["Test passes"],
                    "verification": {"command": "echo ok", "timeout_seconds": 60},
                },
            ]
        }
        graph_file = tmp_path / "task-graph.json"
        graph_file.write_text(json.dumps(graph_data))

        rc = RushCommand()
        result = rc.execute(
            graph_path=graph_file,
            dry_run=True,
        )

        # Circular dependency should be caught during load
        assert result.validated is False
        assert len(result.errors) > 0
        assert "Circular dependency" in result.errors[0]


class TestFeatureName:
    """Tests for feature name extraction."""

    def test_get_feature_name_from_graph_path(self, tmp_path):
        """Test extracting feature name from graph path."""
        from rush import RushCommand

        # Create path like .gsd/specs/my-feature/task-graph.json
        feature_dir = tmp_path / ".gsd" / "specs" / "my-feature"
        feature_dir.mkdir(parents=True)
        graph_file = feature_dir / "task-graph.json"
        graph_file.write_text('{"tasks": []}')

        rc = RushCommand()
        name = rc._get_feature_name(graph_file)
        assert name == "my-feature"

    def test_get_feature_name_default(self, tmp_path):
        """Test default feature name."""
        from rush import RushCommand

        graph_file = tmp_path / "task-graph.json"
        graph_file.write_text('{"tasks": []}')

        rc = RushCommand()
        name = rc._get_feature_name(graph_file)
        assert name == "default"


class TestResumeExecution:
    """Tests for resume functionality."""

    @patch("rush.ExecutionState")
    def test_resume_loads_existing_state(self, mock_state_class, tmp_path):
        """Test resume loads existing execution state."""
        from rush import RushCommand

        # Create mock state
        mock_state = MagicMock()
        mock_state.execution_id = "existing-001"
        mock_state_class.load.return_value = mock_state

        # Create graph file
        graph_file = tmp_path / "task-graph.json"
        graph_file.write_text('{"tasks": []}')

        rc = RushCommand()
        # Mock the orchestrator
        rc.orchestrator = MagicMock()
        rc.orchestrator.start.return_value = None

        rc.execute(
            graph_path=graph_file,
            resume=True,
            dry_run=True,
        )

        # Should have called load
        mock_state_class.load.assert_called()


class TestGraphLoading:
    """Tests for task graph loading."""

    def test_load_graph_from_file(self, tmp_path):
        """Test loading task graph from file."""
        from rush import RushCommand

        graph_data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "Test",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": ["test.py"], "modify": [], "read": []},
                    "acceptance_criteria": ["Test passes"],
                    "verification": {"command": "echo ok", "timeout_seconds": 60},
                }
            ]
        }
        graph_file = tmp_path / "task-graph.json"
        graph_file.write_text(json.dumps(graph_data))

        rc = RushCommand()
        graph = rc._load_graph(graph_file)
        assert len(graph.tasks) == 1
        assert graph.tasks["TASK-001"].id == "TASK-001"

    def test_load_graph_missing_file(self, tmp_path):
        """Test loading missing graph file raises error."""
        from rush import GraphLoadError, RushCommand

        graph_file = tmp_path / "nonexistent.json"

        rc = RushCommand()
        try:
            rc._load_graph(graph_file)
            raise AssertionError("Should have raised GraphLoadError")
        except GraphLoadError:
            pass


class TestWorkerCount:
    """Tests for worker count configuration."""

    def test_default_worker_count(self):
        """Test default worker count."""
        from rush import RushCommand

        rc = RushCommand()
        assert rc.default_workers == 5

    def test_custom_worker_count(self, tmp_path):
        """Test custom worker count."""
        from rush import RushCommand

        graph_file = tmp_path / "task-graph.json"
        graph_file.write_text('{"tasks": []}')

        rc = RushCommand()
        rc.orchestrator = MagicMock()

        rc.execute(
            graph_path=graph_file,
            workers=10,
            dry_run=True,
        )
        # Should validate with requested workers
        assert True  # No exception means success


class TestExecutionSummary:
    """Tests for execution summary generation."""

    def test_summary_includes_task_counts(self, tmp_path):
        """Test summary includes task counts."""
        from rush import RushCommand

        graph_data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "Test",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": ["test.py"], "modify": [], "read": []},
                    "acceptance_criteria": ["Test passes"],
                    "verification": {"command": "echo ok", "timeout_seconds": 60},
                }
            ]
        }
        graph_file = tmp_path / "task-graph.json"
        graph_file.write_text(json.dumps(graph_data))

        rc = RushCommand()
        summary = rc._generate_summary(graph_file)

        assert "total_tasks" in summary
        assert summary["total_tasks"] == 1
