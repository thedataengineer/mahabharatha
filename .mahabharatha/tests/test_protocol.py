"""Tests for MAHABHARATHA v2 Worker Protocol."""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from messages import (
    AssignMessage,
    CompleteMessage,
    FailedMessage,
    Message,
    MessageType,
)
from protocol import (
    CONTEXT_THRESHOLD,
    WorkerProtocol,
    WorkerState,
    check_context_threshold,
    create_checkpoint_signal,
)


class TestWorkerState:
    """Tests for WorkerState enum."""

    def test_state_values(self):
        """Test WorkerState has required values."""
        assert WorkerState.IDLE.value == "idle"
        assert WorkerState.ASSIGNED.value == "assigned"
        assert WorkerState.EXECUTING.value == "executing"
        assert WorkerState.VERIFYING.value == "verifying"
        assert WorkerState.SELF_REVIEW.value == "self_review"
        assert WorkerState.COMPLETE.value == "complete"
        assert WorkerState.FAILED.value == "failed"
        assert WorkerState.BLOCKED.value == "blocked"
        assert WorkerState.WAITING.value == "waiting"


class TestWorkerProtocol:
    """Tests for WorkerProtocol class."""

    def test_initial_state(self):
        """Test worker starts in IDLE state."""
        wp = WorkerProtocol("w1")
        assert wp.state == WorkerState.IDLE

    def test_can_accept_task_when_idle(self):
        """Test worker can accept task only when idle."""
        wp = WorkerProtocol("w1")
        assert wp.can_accept_task()

        wp.transition(WorkerState.ASSIGNED)
        assert not wp.can_accept_task()

    def test_valid_transition_path(self):
        """Test complete valid transition path."""
        wp = WorkerProtocol("w1")
        path = [
            WorkerState.ASSIGNED,
            WorkerState.EXECUTING,
            WorkerState.VERIFYING,
            WorkerState.SELF_REVIEW,
            WorkerState.COMPLETE,
        ]
        for state in path:
            assert wp.transition(state), f"Failed to transition to {state}"

    def test_invalid_transition_skip_assigned(self):
        """Test can't skip ASSIGNED state."""
        wp = WorkerProtocol("w1")
        assert not wp.transition(WorkerState.EXECUTING)

    def test_invalid_transition_assigned_to_complete(self):
        """Test can't go from ASSIGNED to COMPLETE directly."""
        wp = WorkerProtocol("w1")
        wp.transition(WorkerState.ASSIGNED)
        assert not wp.transition(WorkerState.COMPLETE)

    def test_blocked_recovery(self):
        """Test can recover from BLOCKED state."""
        wp = WorkerProtocol("w1")
        wp.transition(WorkerState.ASSIGNED)
        wp.transition(WorkerState.EXECUTING)
        wp.transition(WorkerState.BLOCKED)
        # Can recover from blocked
        assert wp.transition(WorkerState.EXECUTING)

    def test_failed_to_idle(self):
        """Test failed transitions back to idle."""
        wp = WorkerProtocol("w1")
        wp.transition(WorkerState.ASSIGNED)
        wp.transition(WorkerState.EXECUTING)
        wp.transition(WorkerState.FAILED)
        assert wp.transition(WorkerState.IDLE)

    def test_revision_from_self_review(self):
        """Test revision path from SELF_REVIEW back to EXECUTING."""
        wp = WorkerProtocol("w1")
        wp.transition(WorkerState.ASSIGNED)
        wp.transition(WorkerState.EXECUTING)
        wp.transition(WorkerState.VERIFYING)
        wp.transition(WorkerState.SELF_REVIEW)
        # Revision needed
        assert wp.transition(WorkerState.EXECUTING)


class TestContextThreshold:
    """Tests for context threshold handling."""

    def test_threshold_value(self):
        """Test threshold is 70%."""
        assert CONTEXT_THRESHOLD == 0.70

    def test_below_threshold(self):
        """Test below threshold returns False."""
        assert check_context_threshold(0.69) is False
        assert check_context_threshold(0.50) is False
        assert check_context_threshold(0.0) is False

    def test_at_threshold(self):
        """Test at threshold returns True."""
        assert check_context_threshold(0.70) is True

    def test_above_threshold(self):
        """Test above threshold returns True."""
        assert check_context_threshold(0.85) is True
        assert check_context_threshold(1.0) is True


class TestCheckpointSignal:
    """Tests for checkpoint signal creation."""

    def test_create_checkpoint_signal(self):
        """Test checkpoint signal message creation."""
        msg = create_checkpoint_signal(
            task_id="TASK-001",
            worker_id="worker-1",
            current_step=5,
            files_created=["new.py"],
            files_modified=["existing.py"],
        )
        assert msg.type == MessageType.CONTEXT_THRESHOLD
        assert msg.worker_id == "worker-1"
        assert msg.payload["task_id"] == "TASK-001"
        assert msg.payload["current_step"] == 5
        assert msg.payload["checkpoint_ready"] is True


class TestMessageTypes:
    """Tests for message type definitions."""

    def test_message_types_exist(self):
        """Test all required message types exist."""
        assert MessageType.ASSIGN.value == "assign"
        assert MessageType.HEARTBEAT.value == "heartbeat"
        assert MessageType.PROGRESS.value == "progress"
        assert MessageType.COMPLETE.value == "complete"
        assert MessageType.FAILED.value == "failed"
        assert MessageType.BLOCKED.value == "blocked"
        assert MessageType.CONTEXT_THRESHOLD.value == "context_threshold"

    def test_base_message(self):
        """Test base Message creation."""
        msg = Message(
            type=MessageType.HEARTBEAT,
            worker_id="w1",
            timestamp=datetime.now(),
            payload={"status": "ok"},
        )
        assert msg.type == MessageType.HEARTBEAT
        assert msg.worker_id == "w1"

    def test_assign_message(self):
        """Test AssignMessage creation."""
        msg = AssignMessage(
            type=MessageType.ASSIGN,
            worker_id="w1",
            timestamp=datetime.now(),
            payload={},
            task_id="TASK-001",
            spec_path="/path/to/spec.md",
            worktree_path="/path/to/worktree",
            timeout_seconds=1800,
        )
        assert msg.task_id == "TASK-001"
        assert msg.timeout_seconds == 1800

    def test_complete_message(self):
        """Test CompleteMessage creation."""
        msg = CompleteMessage(
            type=MessageType.COMPLETE,
            worker_id="w1",
            timestamp=datetime.now(),
            payload={},
            task_id="TASK-001",
            files_created=["new.py"],
            files_modified=["old.py"],
            verification_passed=True,
            verification_output="All tests pass",
        )
        assert msg.verification_passed is True
        assert "new.py" in msg.files_created

    def test_failed_message(self):
        """Test FailedMessage creation."""
        msg = FailedMessage(
            type=MessageType.FAILED,
            worker_id="w1",
            timestamp=datetime.now(),
            payload={},
            task_id="TASK-001",
            error="Test failed",
            recoverable=True,
            checkpoint_path="/path/to/checkpoint.json",
        )
        assert msg.recoverable is True
        assert "Test failed" in msg.error
