"""Tests for MAHABHARATHA v2 Task Graph."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from task_graph import Task, TaskFiles, TaskGraph, VerificationConfig


class TestTaskFiles:
    """Tests for TaskFiles dataclass."""

    def test_task_files_creation(self):
        """Test TaskFiles can be created."""
        tf = TaskFiles(create=["new.py"], modify=["old.py"], read=["ref.py"])
        assert "new.py" in tf.create
        assert "old.py" in tf.modify
        assert "ref.py" in tf.read


class TestTask:
    """Tests for Task dataclass."""

    def test_task_creation(self):
        """Test Task can be created."""
        t = Task(
            id="TASK-001",
            title="Test Task",
            description="A test task",
            level=0,
            dependencies=[],
            files=TaskFiles(create=[], modify=[], read=[]),
            acceptance_criteria=["Works"],
            verification=VerificationConfig(command="echo test"),
            agents_required=[],
        )
        assert t.id == "TASK-001"
        assert t.level == 0


class TestTaskGraphBasics:
    """Tests for basic TaskGraph functionality."""

    def test_from_dict(self):
        """Test creating TaskGraph from dict."""
        data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "First",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": ["a.py"], "modify": [], "read": []},
                    "acceptance_criteria": ["Done"],
                    "verification": {"command": "echo ok"},
                }
            ]
        }
        g = TaskGraph.from_dict(data)
        assert len(g.tasks) == 1
        assert "TASK-001" in g.tasks

    def test_from_file(self, tmp_path):
        """Test loading TaskGraph from JSON file."""
        data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "First",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": ["a.py"], "modify": [], "read": []},
                    "acceptance_criteria": ["Done"],
                    "verification": {"command": "echo ok"},
                }
            ]
        }
        path = tmp_path / "graph.json"
        path.write_text(json.dumps(data))

        g = TaskGraph.from_file(str(path))
        assert len(g.tasks) == 1

    def test_level_count(self, tmp_path):
        """Test level_count property."""
        data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "L0",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": [], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
                {
                    "id": "TASK-002",
                    "title": "L1",
                    "level": 1,
                    "dependencies": ["TASK-001"],
                    "files": {"create": [], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
            ]
        }
        path = tmp_path / "graph.json"
        path.write_text(json.dumps(data))

        g = TaskGraph.from_file(str(path))
        assert g.level_count == 2

    def test_get_level_tasks(self, tmp_path):
        """Test get_level_tasks method."""
        data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "L0-A",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": ["a.py"], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
                {
                    "id": "TASK-002",
                    "title": "L0-B",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": ["b.py"], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
                {
                    "id": "TASK-003",
                    "title": "L1",
                    "level": 1,
                    "dependencies": ["TASK-001"],
                    "files": {"create": [], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
            ]
        }
        path = tmp_path / "graph.json"
        path.write_text(json.dumps(data))

        g = TaskGraph.from_file(str(path))
        l0_tasks = g.get_level_tasks(0)
        assert len(l0_tasks) == 2
        l1_tasks = g.get_level_tasks(1)
        assert len(l1_tasks) == 1


class TestReadyTasks:
    """Tests for get_ready_tasks method."""

    def test_get_ready_tasks_empty_completed(self, tmp_path):
        """Test getting ready tasks with no completions."""
        data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "L0",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": [], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
                {
                    "id": "TASK-002",
                    "title": "L1",
                    "level": 1,
                    "dependencies": ["TASK-001"],
                    "files": {"create": [], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
            ]
        }
        path = tmp_path / "graph.json"
        path.write_text(json.dumps(data))

        g = TaskGraph.from_file(str(path))
        ready = g.get_ready_tasks(completed=set())
        assert len(ready) == 1
        assert ready[0].id == "TASK-001"

    def test_get_ready_tasks_after_completion(self, tmp_path):
        """Test getting ready tasks after completing dependencies."""
        data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "L0",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": [], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
                {
                    "id": "TASK-002",
                    "title": "L1",
                    "level": 1,
                    "dependencies": ["TASK-001"],
                    "files": {"create": [], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
            ]
        }
        path = tmp_path / "graph.json"
        path.write_text(json.dumps(data))

        g = TaskGraph.from_file(str(path))
        ready = g.get_ready_tasks(completed={"TASK-001"})
        assert len(ready) == 1
        assert ready[0].id == "TASK-002"


class TestCircularDependencyDetection:
    """Tests for circular dependency detection."""

    def test_detect_simple_cycle(self, tmp_path):
        """Test detection of A -> B -> A cycle."""
        data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "A",
                    "level": 0,
                    "dependencies": ["TASK-002"],
                    "files": {"create": [], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
                {
                    "id": "TASK-002",
                    "title": "B",
                    "level": 0,
                    "dependencies": ["TASK-001"],
                    "files": {"create": [], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
            ]
        }
        path = tmp_path / "graph.json"
        path.write_text(json.dumps(data))

        with pytest.raises(ValueError, match="[Cc]ircular"):
            TaskGraph.from_file(str(path))

    def test_detect_longer_cycle(self, tmp_path):
        """Test detection of A -> B -> C -> A cycle."""
        data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "A",
                    "level": 0,
                    "dependencies": ["TASK-003"],
                    "files": {"create": [], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
                {
                    "id": "TASK-002",
                    "title": "B",
                    "level": 0,
                    "dependencies": ["TASK-001"],
                    "files": {"create": [], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
                {
                    "id": "TASK-003",
                    "title": "C",
                    "level": 0,
                    "dependencies": ["TASK-002"],
                    "files": {"create": [], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
            ]
        }
        path = tmp_path / "graph.json"
        path.write_text(json.dumps(data))

        with pytest.raises(ValueError, match="[Cc]ircular"):
            TaskGraph.from_file(str(path))


class TestFileOwnership:
    """Tests for file ownership validation."""

    def test_no_conflict(self, tmp_path):
        """Test no errors when no conflicts."""
        data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "A",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": ["a.py"], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
                {
                    "id": "TASK-002",
                    "title": "B",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": ["b.py"], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
            ]
        }
        path = tmp_path / "graph.json"
        path.write_text(json.dumps(data))

        g = TaskGraph.from_file(str(path))
        errors = g.validate_file_ownership()
        assert errors == []

    def test_detect_create_conflict(self, tmp_path):
        """Test detecting two tasks creating same file."""
        data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "A",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": ["shared.py"], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
                {
                    "id": "TASK-002",
                    "title": "B",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": ["shared.py"], "modify": [], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
            ]
        }
        path = tmp_path / "graph.json"
        path.write_text(json.dumps(data))

        g = TaskGraph.from_file(str(path))
        errors = g.validate_file_ownership()
        assert len(errors) == 1
        assert "shared.py" in errors[0]

    def test_detect_modify_conflict(self, tmp_path):
        """Test detecting two tasks modifying same file."""
        data = {
            "tasks": [
                {
                    "id": "TASK-001",
                    "title": "A",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": [], "modify": ["common.py"], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
                {
                    "id": "TASK-002",
                    "title": "B",
                    "level": 0,
                    "dependencies": [],
                    "files": {"create": [], "modify": ["common.py"], "read": []},
                    "acceptance_criteria": [],
                    "verification": {"command": "echo"},
                },
            ]
        }
        path = tmp_path / "graph.json"
        path.write_text(json.dumps(data))

        g = TaskGraph.from_file(str(path))
        errors = g.validate_file_ownership()
        assert len(errors) == 1
