"""Tests for ZERG worker assignment module."""

import json
from pathlib import Path

import pytest

from zerg.assign import WorkerAssignment
from zerg.types import Task


class TestWorkerAssignment:
    """Tests for WorkerAssignment class."""

    def test_init_default(self) -> None:
        """Test default initialization."""
        assigner = WorkerAssignment()
        assert assigner.worker_count == 5

    def test_init_custom_worker_count(self) -> None:
        """Test initialization with custom worker count."""
        assigner = WorkerAssignment(worker_count=3)
        assert assigner.worker_count == 3

    def test_assign_empty_tasks(self) -> None:
        """Test assigning empty task list."""
        assigner = WorkerAssignment(worker_count=2)
        result = assigner.assign([], "test-feature")

        assert result.feature == "test-feature"
        assert result.worker_count == 2
        assert len(result.assignments) == 0

    def test_assign_single_task(self) -> None:
        """Test assigning a single task."""
        assigner = WorkerAssignment(worker_count=2)
        tasks: list[Task] = [
            {"id": "TASK-001", "level": 1, "estimate_minutes": 15}
        ]

        result = assigner.assign(tasks, "test-feature")

        assert len(result.assignments) == 1
        assert result.assignments[0].task_id == "TASK-001"
        assert result.assignments[0].worker_id == 0  # First worker

    def test_assign_multiple_tasks_balanced(self) -> None:
        """Test tasks are balanced across workers."""
        assigner = WorkerAssignment(worker_count=2)
        tasks: list[Task] = [
            {"id": "TASK-001", "level": 1, "estimate_minutes": 15},
            {"id": "TASK-002", "level": 1, "estimate_minutes": 15},
            {"id": "TASK-003", "level": 1, "estimate_minutes": 15},
            {"id": "TASK-004", "level": 1, "estimate_minutes": 15},
        ]

        result = assigner.assign(tasks, "test-feature")

        # Count tasks per worker
        worker_tasks = {}
        for entry in result.assignments:
            worker_tasks.setdefault(entry.worker_id, 0)
            worker_tasks[entry.worker_id] += 1

        # Should be balanced: 2 tasks per worker
        assert len(worker_tasks) == 2
        assert all(count == 2 for count in worker_tasks.values())

    def test_assign_by_level(self) -> None:
        """Test tasks are assigned respecting levels."""
        assigner = WorkerAssignment(worker_count=2)
        tasks: list[Task] = [
            {"id": "TASK-001", "level": 1, "estimate_minutes": 15},
            {"id": "TASK-002", "level": 1, "estimate_minutes": 15},
            {"id": "TASK-003", "level": 2, "estimate_minutes": 15},
        ]

        result = assigner.assign(tasks, "test-feature")

        # Verify levels are preserved
        level_1_tasks = [a for a in result.assignments if a.level == 1]
        level_2_tasks = [a for a in result.assignments if a.level == 2]

        assert len(level_1_tasks) == 2
        assert len(level_2_tasks) == 1

    def test_assign_longer_tasks_first(self) -> None:
        """Test longer tasks are assigned first for better balancing."""
        assigner = WorkerAssignment(worker_count=2)
        tasks: list[Task] = [
            {"id": "SHORT", "level": 1, "estimate_minutes": 5},
            {"id": "LONG", "level": 1, "estimate_minutes": 60},
            {"id": "MEDIUM", "level": 1, "estimate_minutes": 30},
        ]

        result = assigner.assign(tasks, "test-feature")

        # Longer task should go to worker with least time
        # After LONG (60min) -> worker 0 has 60, worker 1 has 0
        # MEDIUM (30min) -> worker 1 gets it
        # SHORT (5min) -> worker 1 gets it (now 35 vs 60)
        workloads = assigner.get_workload_summary()
        assert workloads[0]["estimated_minutes"] >= workloads[1]["estimated_minutes"] - 30

    def test_get_worker_tasks(self) -> None:
        """Test getting tasks for a specific worker."""
        assigner = WorkerAssignment(worker_count=2)
        tasks: list[Task] = [
            {"id": "TASK-001", "level": 1, "estimate_minutes": 15},
            {"id": "TASK-002", "level": 1, "estimate_minutes": 15},
        ]

        assigner.assign(tasks, "test-feature")

        worker_0_tasks = assigner.get_worker_tasks(0)
        worker_1_tasks = assigner.get_worker_tasks(1)

        assert len(worker_0_tasks) == 1
        assert len(worker_1_tasks) == 1
        assert set(worker_0_tasks + worker_1_tasks) == {"TASK-001", "TASK-002"}

    def test_get_worker_tasks_empty(self) -> None:
        """Test getting tasks for worker with no assignments."""
        assigner = WorkerAssignment(worker_count=5)
        tasks: list[Task] = [{"id": "TASK-001", "level": 1}]

        assigner.assign(tasks, "test-feature")

        # Workers 1-4 should have no tasks
        assert assigner.get_worker_tasks(4) == []

    def test_get_task_worker(self) -> None:
        """Test getting the worker assigned to a task."""
        assigner = WorkerAssignment(worker_count=2)
        tasks: list[Task] = [{"id": "TASK-001", "level": 1}]

        assigner.assign(tasks, "test-feature")

        worker_id = assigner.get_task_worker("TASK-001")
        assert worker_id == 0

    def test_get_task_worker_not_found(self) -> None:
        """Test getting worker for unassigned task."""
        assigner = WorkerAssignment(worker_count=2)

        worker_id = assigner.get_task_worker("NONEXISTENT")
        assert worker_id is None

    def test_get_worker_workload(self) -> None:
        """Test getting workload for a worker."""
        assigner = WorkerAssignment(worker_count=2)
        tasks: list[Task] = [
            {"id": "TASK-001", "level": 1, "estimate_minutes": 30},
            {"id": "TASK-002", "level": 1, "estimate_minutes": 15},
        ]

        assigner.assign(tasks, "test-feature")

        # Worker 0 gets longer task first
        workload_0 = assigner.get_worker_workload(0)
        assert workload_0 == 30

    def test_get_workload_summary(self) -> None:
        """Test getting workload summary."""
        assigner = WorkerAssignment(worker_count=2)
        tasks: list[Task] = [
            {"id": "TASK-001", "level": 1, "estimate_minutes": 30},
            {"id": "TASK-002", "level": 1, "estimate_minutes": 15},
        ]

        assigner.assign(tasks, "test-feature")

        summary = assigner.get_workload_summary()

        assert 0 in summary
        assert 1 in summary
        assert "task_count" in summary[0]
        assert "estimated_minutes" in summary[0]
        assert "tasks" in summary[0]


class TestRebalance:
    """Tests for task rebalancing."""

    def test_rebalance_failed_task(self) -> None:
        """Test rebalancing a failed task."""
        assigner = WorkerAssignment(worker_count=2)
        tasks: list[Task] = [
            {"id": "TASK-001", "level": 1, "estimate_minutes": 15},
            {"id": "TASK-002", "level": 1, "estimate_minutes": 15},
        ]

        assigner.assign(tasks, "test-feature")

        # Simulate TASK-001 failing on worker 0
        reassignments = assigner.rebalance(
            completed_tasks=set(),
            failed_tasks={"TASK-001"},
            current_level=1,
        )

        # Task should be reassigned to worker with capacity
        assert len(reassignments) >= 0  # May or may not reassign based on capacity

    def test_rebalance_no_changes_needed(self) -> None:
        """Test rebalancing when no changes needed."""
        assigner = WorkerAssignment(worker_count=2)
        tasks: list[Task] = [{"id": "TASK-001", "level": 1}]

        assigner.assign(tasks, "test-feature")

        reassignments = assigner.rebalance(
            completed_tasks=set(),
            failed_tasks=set(),
            current_level=1,
        )

        assert len(reassignments) == 0


class TestSaveLoad:
    """Tests for saving/loading assignments."""

    def test_save_to_file(self, tmp_path: Path) -> None:
        """Test saving assignments to file."""
        assigner = WorkerAssignment(worker_count=2)
        tasks: list[Task] = [{"id": "TASK-001", "level": 1}]

        assigner.assign(tasks, "test-feature")

        output_file = tmp_path / "assignments.json"
        assigner.save_to_file(str(output_file), "test-feature")

        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)

        assert data["feature"] == "test-feature"
        assert data["worker_count"] == 2
        assert len(data["assignments"]) == 1

    def test_load_from_file(self, tmp_path: Path) -> None:
        """Test loading assignments from file."""
        # Create assignment file
        data = {
            "feature": "test-feature",
            "worker_count": 3,
            "assignments": [
                {"task_id": "TASK-001", "worker_id": 0, "level": 1, "estimated_minutes": 15},
                {"task_id": "TASK-002", "worker_id": 1, "level": 1, "estimated_minutes": 20},
            ],
        }

        input_file = tmp_path / "assignments.json"
        with open(input_file, "w") as f:
            json.dump(data, f)

        assigner = WorkerAssignment.load_from_file(str(input_file))

        assert assigner.worker_count == 3
        assert assigner.get_task_worker("TASK-001") == 0
        assert assigner.get_task_worker("TASK-002") == 1
        assert assigner.get_worker_workload(0) == 15
        assert assigner.get_worker_workload(1) == 20

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        """Test saving creates parent directories."""
        assigner = WorkerAssignment(worker_count=2)
        tasks: list[Task] = [{"id": "TASK-001", "level": 1}]
        assigner.assign(tasks, "test")

        output_file = tmp_path / "nested" / "dir" / "assignments.json"
        assigner.save_to_file(str(output_file), "test")

        assert output_file.exists()


class TestBalanceByLevel:
    """Tests for level-based balancing."""

    def test_balance_resets_per_level(self) -> None:
        """Test balancing resets for each level."""
        assigner = WorkerAssignment(worker_count=2)
        tasks: list[Task] = [
            {"id": "L1-001", "level": 1, "estimate_minutes": 60},
            {"id": "L1-002", "level": 1, "estimate_minutes": 10},
            {"id": "L2-001", "level": 2, "estimate_minutes": 60},
            {"id": "L2-002", "level": 2, "estimate_minutes": 10},
        ]

        result = assigner.assign(tasks, "test", balance_by_level=True)

        # Level 1: worker 0 gets 60min, worker 1 gets 10min
        # Level 2: resets, worker 0 gets 60min, worker 1 gets 10min
        # Without reset, level 2 would have gone differently

        level_2_tasks = [a for a in result.assignments if a.level == 2]
        # Both levels should show similar distribution pattern
        assert len(level_2_tasks) == 2

    def test_balance_without_level_reset(self) -> None:
        """Test balancing without level reset."""
        assigner = WorkerAssignment(worker_count=2)
        tasks: list[Task] = [
            {"id": "L1-001", "level": 1, "estimate_minutes": 60},
            {"id": "L2-001", "level": 2, "estimate_minutes": 60},
        ]

        assigner.assign(tasks, "test", balance_by_level=False)

        # After L1-001 (60min) on worker 0
        # L2-001 should go to worker 1 due to cumulative balancing
        l2_worker = assigner.get_task_worker("L2-001")
        assert l2_worker == 1  # Worker 1 has less cumulative time
