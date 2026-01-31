"""Integration tests for StateManager persistence.

Tests cover:
1. State save and load roundtrip
2. State recovery after crash
3. Concurrent state access handling
4. State migration between versions
5. State backup and restore
"""

import json
import os
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from zerg.constants import LevelMergeStatus, TaskStatus, WorkerStatus
from zerg.exceptions import StateError
from zerg.state import StateManager
from zerg.types import FeatureMetrics, LevelMetrics, WorkerMetrics, WorkerState


class TestStateSaveLoadRoundtrip:
    """Test state save and load roundtrip with real filesystem operations."""

    def test_basic_roundtrip(self, tmp_path: Path) -> None:
        """Test basic save/load preserves state."""
        state_dir = tmp_path / "state"
        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        # Set up comprehensive state
        manager.set_current_level(3)
        manager.set_task_status("TASK-001", TaskStatus.COMPLETE, worker_id=0)
        manager.set_task_status("TASK-002", TaskStatus.IN_PROGRESS, worker_id=1)
        manager.set_task_status("TASK-003", TaskStatus.PENDING)
        manager.set_paused(True)
        manager.set_error("Test error message")
        manager.append_event("test_event", {"key": "value"})
        manager.set_level_status(1, "complete", merge_commit="abc123")
        manager.set_level_merge_status(2, LevelMergeStatus.MERGING)

        # Create new manager instance and verify state persisted
        manager2 = StateManager("test-feature", state_dir=state_dir)
        state = manager2.load()

        assert state["current_level"] == 3
        assert state["paused"] is True
        assert state["error"] == "Test error message"
        assert len(state["execution_log"]) == 1
        assert state["execution_log"][0]["event"] == "test_event"
        assert manager2.get_task_status("TASK-001") == TaskStatus.COMPLETE.value
        assert manager2.get_task_status("TASK-002") == TaskStatus.IN_PROGRESS.value
        assert manager2.get_task_status("TASK-003") == TaskStatus.PENDING.value
        assert manager2.get_level_merge_status(2) == LevelMergeStatus.MERGING

    def test_worker_state_roundtrip(self, tmp_path: Path) -> None:
        """Test worker state serialization roundtrip."""
        state_dir = tmp_path / "state"
        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        # Create worker states with all fields populated
        now = datetime.now()
        worker_state = WorkerState(
            worker_id=1,
            status=WorkerStatus.RUNNING,
            current_task="TASK-001",
            port=49152,
            container_id="container-abc",
            worktree_path="/path/to/worktree",
            branch="feature/test",
            health_check_at=now,
            started_at=now,
            ready_at=now,
            last_task_completed_at=now,
            tasks_completed=5,
            context_usage=0.75,
        )
        manager.set_worker_state(worker_state)

        # Load in new manager instance
        manager2 = StateManager("test-feature", state_dir=state_dir)
        manager2.load()
        loaded_worker = manager2.get_worker_state(1)

        assert loaded_worker is not None
        assert loaded_worker.worker_id == 1
        assert loaded_worker.status == WorkerStatus.RUNNING
        assert loaded_worker.current_task == "TASK-001"
        assert loaded_worker.port == 49152
        assert loaded_worker.container_id == "container-abc"
        assert loaded_worker.worktree_path == "/path/to/worktree"
        assert loaded_worker.branch == "feature/test"
        assert loaded_worker.tasks_completed == 5
        assert loaded_worker.context_usage == 0.75

    def test_metrics_roundtrip(self, tmp_path: Path) -> None:
        """Test metrics serialization roundtrip."""
        state_dir = tmp_path / "state"
        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        # Create comprehensive metrics
        metrics = FeatureMetrics(
            computed_at=datetime.now(),
            total_duration_ms=120000,
            workers_used=3,
            tasks_total=10,
            tasks_completed=8,
            tasks_failed=2,
            levels_completed=2,
            worker_metrics=[
                WorkerMetrics(
                    worker_id=0,
                    initialization_ms=5000,
                    uptime_ms=60000,
                    tasks_completed=3,
                    tasks_failed=1,
                    total_task_duration_ms=45000,
                    avg_task_duration_ms=15000.0,
                ),
                WorkerMetrics(
                    worker_id=1,
                    initialization_ms=4500,
                    uptime_ms=55000,
                    tasks_completed=5,
                    tasks_failed=1,
                    total_task_duration_ms=50000,
                    avg_task_duration_ms=10000.0,
                ),
            ],
            level_metrics=[
                LevelMetrics(
                    level=1,
                    duration_ms=40000,
                    task_count=5,
                    completed_count=5,
                    failed_count=0,
                    avg_task_duration_ms=8000.0,
                    p50_duration_ms=7500,
                    p95_duration_ms=12000,
                ),
            ],
        )
        manager.store_metrics(metrics)

        # Load in new manager instance
        manager2 = StateManager("test-feature", state_dir=state_dir)
        manager2.load()
        loaded_metrics = manager2.get_metrics()

        assert loaded_metrics is not None
        assert loaded_metrics.total_duration_ms == 120000
        assert loaded_metrics.workers_used == 3
        assert loaded_metrics.tasks_total == 10
        assert loaded_metrics.tasks_completed == 8
        assert loaded_metrics.tasks_failed == 2
        assert len(loaded_metrics.worker_metrics) == 2
        assert len(loaded_metrics.level_metrics) == 1
        assert loaded_metrics.worker_metrics[0].avg_task_duration_ms == 15000.0

    def test_large_event_log_roundtrip(self, tmp_path: Path) -> None:
        """Test roundtrip with large execution log."""
        state_dir = tmp_path / "state"
        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        # Add many events
        for i in range(100):
            manager.append_event(f"event_{i}", {"index": i, "data": "x" * 100})

        # Load in new manager
        manager2 = StateManager("test-feature", state_dir=state_dir)
        state = manager2.load()

        assert len(state["execution_log"]) == 100
        assert state["execution_log"][50]["event"] == "event_50"
        assert state["execution_log"][50]["data"]["index"] == 50


class TestStateRecoveryAfterCrash:
    """Test state recovery scenarios simulating crashes."""

    def test_recovery_from_valid_state(self, tmp_path: Path) -> None:
        """Test recovery when state file is valid."""
        state_dir = tmp_path / "state"
        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        # Set up state simulating mid-execution
        manager.set_current_level(2)
        manager.set_task_status("TASK-001", TaskStatus.COMPLETE, worker_id=0)
        manager.set_task_status("TASK-002", TaskStatus.IN_PROGRESS, worker_id=1)
        manager.set_task_status("TASK-003", TaskStatus.PENDING)
        manager.set_level_status(1, "complete")
        manager.set_level_status(2, "running")

        # Simulate crash by creating new manager (without explicit shutdown)
        manager2 = StateManager("test-feature", state_dir=state_dir)
        state = manager2.load()

        # Verify recovery preserves in-progress state
        assert state["current_level"] == 2
        assert manager2.get_task_status("TASK-001") == TaskStatus.COMPLETE.value
        assert manager2.get_task_status("TASK-002") == TaskStatus.IN_PROGRESS.value
        assert manager2.get_task_status("TASK-003") == TaskStatus.PENDING.value

    def test_recovery_from_corrupted_json(self, tmp_path: Path) -> None:
        """Test recovery when state file is corrupted JSON."""
        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Write corrupted JSON
        state_file = state_dir / "test-feature.json"
        state_file.write_text("{invalid json content", encoding="utf-8")

        manager = StateManager("test-feature", state_dir=state_dir)

        # Should raise StateError on load
        with pytest.raises(StateError) as exc_info:
            manager.load()
        assert "Failed to parse state file" in str(exc_info.value)

    def test_recovery_from_empty_file(self, tmp_path: Path) -> None:
        """Test recovery when state file is empty."""
        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Write empty file
        state_file = state_dir / "test-feature.json"
        state_file.write_text("", encoding="utf-8")

        manager = StateManager("test-feature", state_dir=state_dir)

        # Should raise StateError on load (empty JSON)
        with pytest.raises(StateError):
            manager.load()

    def test_recovery_from_partial_write(self, tmp_path: Path) -> None:
        """Test recovery when state file has truncated JSON (partial write)."""
        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Write truncated JSON (simulating crash mid-write)
        state_file = state_dir / "test-feature.json"
        state_file.write_text('{"feature": "test", "current_level": 2, "tasks":', encoding="utf-8")

        manager = StateManager("test-feature", state_dir=state_dir)

        # Should raise StateError
        with pytest.raises(StateError):
            manager.load()

    def test_recovery_from_missing_directory(self, tmp_path: Path) -> None:
        """Test state manager creates directory if missing."""
        state_dir = tmp_path / "nonexistent" / "nested" / "state"

        # Directory should not exist
        assert not state_dir.exists()

        manager = StateManager("test-feature", state_dir=state_dir)

        # Directory should be created
        assert state_dir.exists()

        # Should load fresh state
        state = manager.load()
        assert state["feature"] == "test-feature"
        assert state["current_level"] == 0

    def test_recovery_preserves_task_timestamps(self, tmp_path: Path) -> None:
        """Test that task timestamps are preserved after recovery."""
        state_dir = tmp_path / "state"
        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        # Set task status which creates timestamps
        manager.set_task_status("TASK-001", TaskStatus.IN_PROGRESS, worker_id=0)
        time.sleep(0.01)  # Small delay to ensure different timestamp
        manager.set_task_status("TASK-001", TaskStatus.COMPLETE, worker_id=0)

        # Recover in new manager
        manager2 = StateManager("test-feature", state_dir=state_dir)
        manager2.load()

        task_state = manager2._state["tasks"]["TASK-001"]
        assert "started_at" in task_state
        assert "completed_at" in task_state
        assert task_state["started_at"] != task_state["completed_at"]


class TestConcurrentStateAccess:
    """Test concurrent state access handling.

    Note: StateManager uses threading.RLock for thread safety within a single
    instance but does not implement file-level locking for multi-process access.
    These tests verify the thread-safety guarantees provided.
    """

    def test_single_instance_concurrent_task_claims(self, tmp_path: Path) -> None:
        """Test multiple threads claiming tasks through a single shared manager instance."""
        state_dir = tmp_path / "state"
        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        # Set up pending tasks
        for i in range(10):
            manager.set_task_status(f"TASK-{i:03d}", TaskStatus.PENDING)

        results: dict[str, list[int]] = {f"TASK-{i:03d}": [] for i in range(10)}
        lock = threading.Lock()

        def worker_claim(worker_id: int) -> None:
            """Worker attempts to claim tasks using shared manager."""
            for task_id in list(results.keys()):
                if manager.claim_task(task_id, worker_id):
                    with lock:
                        results[task_id].append(worker_id)

        # Run concurrent claims from multiple threads using same manager instance
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker_claim, i) for i in range(5)]
            for future in as_completed(futures):
                future.result()

        # Each task should be claimed by at most one worker
        for task_id, claimers in results.items():
            assert len(claimers) <= 1, f"Task {task_id} claimed by multiple workers: {claimers}"

        # All tasks should be claimed (total claims = 10)
        total_claims = sum(len(v) for v in results.values())
        assert total_claims == 10

    def test_single_instance_concurrent_state_updates(self, tmp_path: Path) -> None:
        """Test concurrent state updates from multiple threads using shared manager."""
        state_dir = tmp_path / "state"
        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        errors: list[Exception] = []
        update_count = 50

        def update_tasks(start_id: int) -> None:
            """Update task statuses using shared manager."""
            try:
                for i in range(update_count):
                    task_id = f"TASK-{start_id}-{i:03d}"
                    manager.set_task_status(task_id, TaskStatus.COMPLETE, worker_id=start_id)
            except Exception as e:
                errors.append(e)

        # Run concurrent updates through shared manager
        threads = [threading.Thread(target=update_tasks, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No errors should occur
        assert len(errors) == 0, f"Errors during concurrent updates: {errors}"

        # Verify all tasks were written
        state = manager.load()
        assert len(state["tasks"]) == 5 * update_count

    def test_single_instance_concurrent_event_logging(self, tmp_path: Path) -> None:
        """Test concurrent event logging through shared manager instance."""
        state_dir = tmp_path / "state"
        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        events_per_thread = 20
        num_threads = 5

        def log_events(thread_id: int) -> None:
            """Log events using shared manager."""
            for i in range(events_per_thread):
                manager.append_event(f"event_t{thread_id}_{i}", {"thread": thread_id, "index": i})

        threads = [threading.Thread(target=log_events, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all events were logged
        state = manager.load()
        assert len(state["execution_log"]) == events_per_thread * num_threads

    def test_lock_prevents_corruption(self, tmp_path: Path) -> None:
        """Test that internal lock prevents state corruption during concurrent access."""
        state_dir = tmp_path / "state"
        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        errors: list[Exception] = []
        iterations = 100

        def read_write_cycle() -> None:
            """Perform read-write cycle on shared manager."""
            try:
                for _ in range(iterations):
                    # Read current level
                    _ = manager.get_current_level()
                    # Write new level
                    manager.set_current_level(manager.get_current_level() + 1)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_write_cycle) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No errors should occur
        assert len(errors) == 0

        # State should be valid
        state = manager.load()
        assert isinstance(state["current_level"], int)

    def test_sequential_multi_instance_access(self, tmp_path: Path) -> None:
        """Test sequential access from multiple manager instances works correctly."""
        state_dir = tmp_path / "state"

        # Create and populate state with first manager
        manager1 = StateManager("test-feature", state_dir=state_dir)
        manager1.load()
        manager1.set_task_status("TASK-001", TaskStatus.PENDING)
        manager1.set_current_level(1)

        # Access with second manager after first is done
        manager2 = StateManager("test-feature", state_dir=state_dir)
        state = manager2.load()
        assert state["current_level"] == 1
        assert manager2.get_task_status("TASK-001") == TaskStatus.PENDING.value

        # Modify with second manager
        manager2.set_task_status("TASK-001", TaskStatus.COMPLETE, worker_id=0)

        # Verify with third manager
        manager3 = StateManager("test-feature", state_dir=state_dir)
        manager3.load()
        assert manager3.get_task_status("TASK-001") == TaskStatus.COMPLETE.value

    def test_worker_state_concurrent_updates(self, tmp_path: Path) -> None:
        """Test concurrent worker state updates through shared manager."""
        state_dir = tmp_path / "state"
        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        num_workers = 5
        updates_per_worker = 10

        def update_worker_state(worker_id: int) -> None:
            """Update worker state repeatedly."""
            for i in range(updates_per_worker):
                worker = WorkerState(
                    worker_id=worker_id,
                    status=WorkerStatus.RUNNING,
                    tasks_completed=i,
                    context_usage=i / updates_per_worker,
                )
                manager.set_worker_state(worker)

        threads = [threading.Thread(target=update_worker_state, args=(i,)) for i in range(num_workers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all workers have final state
        all_workers = manager.get_all_workers()
        assert len(all_workers) == num_workers

        for worker_id in range(num_workers):
            worker = all_workers[worker_id]
            assert worker.worker_id == worker_id
            # Final state should have last update values
            assert worker.tasks_completed == updates_per_worker - 1


class TestStateMigration:
    """Test state migration between versions."""

    def test_load_v1_state_format(self, tmp_path: Path) -> None:
        """Test loading state from older format (missing new fields)."""
        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Create V1 state (missing newer fields like merge_status, metrics)
        v1_state: dict[str, Any] = {
            "feature": "test-feature",
            "started_at": "2026-01-25T10:00:00",
            "current_level": 1,
            "tasks": {
                "TASK-001": {"status": "complete", "worker_id": 0},
                "TASK-002": {"status": "pending"},
            },
            "workers": {},
            "execution_log": [],
            "paused": False,
            "error": None,
            # Note: No "levels" or "metrics" field
        }

        state_file = state_dir / "test-feature.json"
        with open(state_file, "w") as f:
            json.dump(v1_state, f)

        # Load with current manager
        manager = StateManager("test-feature", state_dir=state_dir)
        state = manager.load()

        # Should load without error
        assert state["feature"] == "test-feature"
        assert state["current_level"] == 1
        assert manager.get_task_status("TASK-001") == "complete"
        assert manager.get_task_status("TASK-002") == "pending"

        # Optional fields should be accessible with defaults
        assert manager.get_level_status(1) is None
        assert manager.get_metrics() is None

    def test_migrate_adds_missing_fields(self, tmp_path: Path) -> None:
        """Test that operations work on migrated state."""
        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Create minimal state
        minimal_state: dict[str, Any] = {
            "feature": "test-feature",
            "started_at": "2026-01-25T10:00:00",
            "current_level": 0,
            "tasks": {},
            "workers": {},
            "execution_log": [],
            "paused": False,
            "error": None,
        }

        state_file = state_dir / "test-feature.json"
        with open(state_file, "w") as f:
            json.dump(minimal_state, f)

        # Load and add new features
        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        # These operations should work even though state was minimal
        manager.set_level_status(1, "running")
        manager.set_level_merge_status(1, LevelMergeStatus.PENDING)
        manager.increment_task_retry("TASK-001")

        # Verify they persisted
        manager2 = StateManager("test-feature", state_dir=state_dir)
        manager2.load()

        level_status = manager2.get_level_status(1)
        assert level_status is not None
        assert level_status["status"] == "running"
        assert manager2.get_level_merge_status(1) == LevelMergeStatus.PENDING
        assert manager2.get_task_retry_count("TASK-001") == 1

    def test_state_with_extra_fields(self, tmp_path: Path) -> None:
        """Test loading state with unknown fields (forward compatibility)."""
        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Create state with extra fields that current code doesnt know about
        future_state: dict[str, Any] = {
            "feature": "test-feature",
            "started_at": "2026-01-25T10:00:00",
            "current_level": 2,
            "tasks": {},
            "workers": {},
            "levels": {},
            "execution_log": [],
            "metrics": None,
            "paused": False,
            "error": None,
            # Extra fields from a future version
            "future_field_1": "some value",
            "future_field_2": {"nested": "data"},
            "new_feature_config": [1, 2, 3],
        }

        state_file = state_dir / "test-feature.json"
        with open(state_file, "w") as f:
            json.dump(future_state, f)

        # Should load without error
        manager = StateManager("test-feature", state_dir=state_dir)
        state = manager.load()

        assert state["current_level"] == 2
        # Extra fields are preserved in state dict
        assert state.get("future_field_1") == "some value"

    def test_task_status_enum_compatibility(self, tmp_path: Path) -> None:
        """Test loading task states with string status values."""
        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Create state with string task statuses
        string_status_state: dict[str, Any] = {
            "feature": "test-feature",
            "started_at": "2026-01-25T10:00:00",
            "current_level": 1,
            "tasks": {
                "TASK-001": {"status": "complete"},
                "TASK-002": {"status": "in_progress"},
                "TASK-003": {"status": "pending"},
                "TASK-004": {"status": "failed", "error": "test error"},
            },
            "workers": {},
            "execution_log": [],
            "paused": False,
            "error": None,
        }

        state_file = state_dir / "test-feature.json"
        with open(state_file, "w") as f:
            json.dump(string_status_state, f)

        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        # Should work with both string and enum lookups
        assert manager.get_task_status("TASK-001") == TaskStatus.COMPLETE.value
        assert manager.get_task_status("TASK-002") == TaskStatus.IN_PROGRESS.value

        # get_tasks_by_status should work
        pending = manager.get_tasks_by_status(TaskStatus.PENDING)
        assert "TASK-003" in pending

        failed = manager.get_tasks_by_status("failed")
        assert "TASK-004" in failed


class TestStateBackupRestore:
    """Test state backup and restore functionality."""

    def test_manual_backup_and_restore(self, tmp_path: Path) -> None:
        """Test manual backup and restore of state files."""
        state_dir = tmp_path / "state"
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create and populate state
        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()
        manager.set_current_level(3)
        manager.set_task_status("TASK-001", TaskStatus.COMPLETE, worker_id=0)
        manager.set_task_status("TASK-002", TaskStatus.IN_PROGRESS, worker_id=1)
        manager.append_event("important_event", {"data": "critical"})

        # Manual backup (copy state file)
        state_file = state_dir / "test-feature.json"
        backup_file = backup_dir / "test-feature.json.bak"
        shutil.copy2(state_file, backup_file)

        # Simulate disaster (corrupt or delete state)
        state_file.write_text("corrupted data", encoding="utf-8")

        # Verify state is corrupted
        with pytest.raises(StateError):
            StateManager("test-feature", state_dir=state_dir).load()

        # Restore from backup
        shutil.copy2(backup_file, state_file)

        # Verify restoration
        restored_manager = StateManager("test-feature", state_dir=state_dir)
        state = restored_manager.load()

        assert state["current_level"] == 3
        assert restored_manager.get_task_status("TASK-001") == TaskStatus.COMPLETE.value
        assert restored_manager.get_task_status("TASK-002") == TaskStatus.IN_PROGRESS.value
        assert len(state["execution_log"]) == 1
        assert state["execution_log"][0]["event"] == "important_event"

    def test_backup_multiple_features(self, tmp_path: Path) -> None:
        """Test backing up multiple feature states."""
        state_dir = tmp_path / "state"
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)

        features = ["feature-a", "feature-b", "feature-c"]

        # Create states for multiple features
        for i, feature in enumerate(features):
            manager = StateManager(feature, state_dir=state_dir)
            manager.load()
            manager.set_current_level(i + 1)
            manager.set_task_status(f"TASK-{feature}", TaskStatus.IN_PROGRESS, worker_id=i)

        # Backup all state files
        for state_file in state_dir.glob("*.json"):
            backup_file = backup_dir / f"{state_file.name}.bak"
            shutil.copy2(state_file, backup_file)

        # Delete original states
        for state_file in list(state_dir.glob("*.json")):
            state_file.unlink()

        # Restore all backups
        for backup_file in backup_dir.glob("*.bak"):
            original_name = backup_file.name.replace(".bak", "")
            restored_file = state_dir / original_name
            shutil.copy2(backup_file, restored_file)

        # Verify all features restored
        for i, feature in enumerate(features):
            manager = StateManager(feature, state_dir=state_dir)
            state = manager.load()
            assert state["current_level"] == i + 1
            assert manager.get_task_status(f"TASK-{feature}") == TaskStatus.IN_PROGRESS.value

    def test_incremental_backup_simulation(self, tmp_path: Path) -> None:
        """Test simulated incremental backup by tracking changes."""
        state_dir = tmp_path / "state"
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        backups: list[Path] = []

        # Phase 1: Initial state
        manager.set_current_level(1)
        manager.set_task_status("TASK-001", TaskStatus.PENDING)
        backup_1 = backup_dir / "backup_phase1.json"
        shutil.copy2(state_dir / "test-feature.json", backup_1)
        backups.append(backup_1)

        # Phase 2: Progress
        manager.set_task_status("TASK-001", TaskStatus.IN_PROGRESS, worker_id=0)
        manager.append_event("started", {"task": "TASK-001"})
        backup_2 = backup_dir / "backup_phase2.json"
        shutil.copy2(state_dir / "test-feature.json", backup_2)
        backups.append(backup_2)

        # Phase 3: Completion
        manager.set_task_status("TASK-001", TaskStatus.COMPLETE, worker_id=0)
        manager.set_current_level(2)
        backup_3 = backup_dir / "backup_phase3.json"
        shutil.copy2(state_dir / "test-feature.json", backup_3)
        backups.append(backup_3)

        # Restore to different phases and verify
        # Restore to phase 1
        shutil.copy2(backups[0], state_dir / "test-feature.json")
        m1 = StateManager("test-feature", state_dir=state_dir)
        s1 = m1.load()
        assert s1["current_level"] == 1
        assert m1.get_task_status("TASK-001") == TaskStatus.PENDING.value

        # Restore to phase 2
        shutil.copy2(backups[1], state_dir / "test-feature.json")
        m2 = StateManager("test-feature", state_dir=state_dir)
        s2 = m2.load()
        assert s2["current_level"] == 1
        assert m2.get_task_status("TASK-001") == TaskStatus.IN_PROGRESS.value
        assert len(s2["execution_log"]) == 1

        # Restore to phase 3
        shutil.copy2(backups[2], state_dir / "test-feature.json")
        m3 = StateManager("test-feature", state_dir=state_dir)
        s3 = m3.load()
        assert s3["current_level"] == 2
        assert m3.get_task_status("TASK-001") == TaskStatus.COMPLETE.value

    def test_delete_and_recreate(self, tmp_path: Path) -> None:
        """Test deleting state and recreating fresh."""
        state_dir = tmp_path / "state"
        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        # Populate state
        manager.set_current_level(5)
        manager.set_task_status("TASK-001", TaskStatus.FAILED, error="fatal error")

        # Verify it exists
        assert manager.exists()

        # Delete state
        manager.delete()
        assert not manager.exists()

        # Create fresh manager - should start with initial state
        fresh_manager = StateManager("test-feature", state_dir=state_dir)
        state = fresh_manager.load()

        assert state["current_level"] == 0
        assert state["tasks"] == {}
        assert state["error"] is None

    @pytest.mark.skipif(os.name == "nt", reason="File permission tests not applicable on Windows")
    def test_backup_preserves_file_permissions(self, tmp_path: Path) -> None:
        """Test that backup/restore preserves file attributes."""

        state_dir = tmp_path / "state"
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)

        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()
        manager.set_current_level(1)

        state_file = state_dir / "test-feature.json"
        backup_file = backup_dir / "test-feature.json.bak"

        # Set specific permissions
        original_mode = state_file.stat().st_mode

        # Backup with metadata preservation
        shutil.copy2(state_file, backup_file)

        # Verify backup has same permissions
        backup_mode = backup_file.stat().st_mode
        assert original_mode == backup_mode


class TestStateMdGeneration:
    """Test STATE.md generation functionality."""

    def test_generate_state_md(self, tmp_path: Path) -> None:
        """Test STATE.md file generation."""
        state_dir = tmp_path / "state"
        gsd_dir = tmp_path / ".gsd"
        gsd_dir.mkdir(parents=True, exist_ok=True)

        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        # Set up comprehensive state
        manager.set_current_level(2)
        manager.set_task_status("TASK-001", TaskStatus.COMPLETE, worker_id=0)
        manager.set_task_status("TASK-002", TaskStatus.IN_PROGRESS, worker_id=1)
        manager.set_task_status("TASK-003", TaskStatus.FAILED, worker_id=2, error="Verification failed")
        manager.increment_task_retry("TASK-003")
        manager.set_level_status(1, "complete", merge_commit="abc1234567890")
        manager.set_level_status(2, "running")
        manager.append_event("level_started", {"level": 2})

        # Generate STATE.md
        state_md_path = manager.generate_state_md(gsd_dir=gsd_dir)

        assert state_md_path.exists()
        content = state_md_path.read_text(encoding="utf-8")

        # Verify content
        assert "# ZERG State: test-feature" in content
        assert "**Level:** 2" in content
        assert "TASK-001" in content
        assert "complete" in content
        assert "TASK-003" in content
        assert "Blockers" in content
        assert "Verification failed" in content

    def test_state_md_roundtrip_persistence(self, tmp_path: Path) -> None:
        """Test that STATE.md is regenerated correctly after state changes."""
        state_dir = tmp_path / "state"
        gsd_dir = tmp_path / ".gsd"
        gsd_dir.mkdir(parents=True, exist_ok=True)

        manager = StateManager("test-feature", state_dir=state_dir)
        manager.load()

        # Initial state
        manager.set_current_level(1)
        manager.generate_state_md(gsd_dir=gsd_dir)
        content1 = (gsd_dir / "STATE.md").read_text(encoding="utf-8")
        assert "**Level:** 1" in content1

        # Update state
        manager.set_current_level(3)
        manager.generate_state_md(gsd_dir=gsd_dir)
        content2 = (gsd_dir / "STATE.md").read_text(encoding="utf-8")
        assert "**Level:** 3" in content2
        assert "**Level:** 1" not in content2


class TestCrossProcessStateVisibility:
    """Test that separate StateManager instances see each other's writes after load()."""

    def test_cross_process_state_visibility(self, tmp_path: Path) -> None:
        """Two StateManager instances on same file see each other's writes."""
        state_dir = tmp_path / "state"

        # Instance A (simulating worker process)
        manager_a = StateManager("test-feature", state_dir=state_dir)
        manager_a.load()

        # Instance B (simulating orchestrator process)
        manager_b = StateManager("test-feature", state_dir=state_dir)
        manager_b.load()

        # Worker (A) writes its own WorkerState
        worker_state = WorkerState(
            worker_id=0,
            status=WorkerStatus.RUNNING,
            current_task="TASK-001",
            branch="zerg/test/worker-0",
            worktree_path="/tmp/wt",
            started_at=datetime.now(),
            tasks_completed=2,
            context_usage=0.35,
        )
        manager_a.set_worker_state(worker_state)

        # Orchestrator (B) hasn't reloaded yet — stale in-memory state
        stale_worker = manager_b.get_worker_state(0)
        assert stale_worker is None, "Before load(), B should not see A's write"

        # Orchestrator (B) reloads from disk
        manager_b.load()
        fresh_worker = manager_b.get_worker_state(0)

        assert fresh_worker is not None
        assert fresh_worker.status == WorkerStatus.RUNNING
        assert fresh_worker.current_task == "TASK-001"
        assert fresh_worker.tasks_completed == 2
        assert fresh_worker.context_usage == 0.35

    def test_cross_process_worker_and_orchestrator_non_overlapping(self, tmp_path: Path) -> None:
        """Worker writes worker state, orchestrator writes task state — no clobbering."""
        state_dir = tmp_path / "state"

        # Both start from same initial state
        worker_mgr = StateManager("test-feature", state_dir=state_dir)
        worker_mgr.load()

        orch_mgr = StateManager("test-feature", state_dir=state_dir)
        orch_mgr.load()

        # Orchestrator writes task status
        orch_mgr.set_task_status("TASK-001", TaskStatus.PENDING, worker_id=0)

        # Worker reads latest state, then writes its own worker state
        worker_mgr.load()
        ws = WorkerState(
            worker_id=0,
            status=WorkerStatus.RUNNING,
            current_task="TASK-001",
            branch="zerg/test/worker-0",
            worktree_path="/tmp/wt",
            started_at=datetime.now(),
        )
        worker_mgr.set_worker_state(ws)

        # Orchestrator reloads — should see both task status and worker state
        orch_mgr.load()
        assert orch_mgr.get_task_status("TASK-001") == TaskStatus.PENDING.value
        loaded_ws = orch_mgr.get_worker_state(0)
        assert loaded_ws is not None
        assert loaded_ws.status == WorkerStatus.RUNNING
        assert loaded_ws.current_task == "TASK-001"
