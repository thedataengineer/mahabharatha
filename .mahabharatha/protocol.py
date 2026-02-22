"""MAHABHARATHA v2 Protocol - Worker communication protocol and state machine."""

from datetime import datetime
from enum import Enum

from messages import Message, MessageType

# Context threshold at which workers should checkpoint and exit
CONTEXT_THRESHOLD = 0.70


class WorkerState(Enum):
    """Worker execution states."""

    IDLE = "idle"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    SELF_REVIEW = "self_review"
    COMPLETE = "complete"
    FAILED = "failed"
    BLOCKED = "blocked"
    WAITING = "waiting"  # Context threshold reached


class WorkerProtocol:
    """Manages worker state transitions."""

    VALID_TRANSITIONS: dict[WorkerState, list[WorkerState]] = {
        WorkerState.IDLE: [WorkerState.ASSIGNED],
        WorkerState.ASSIGNED: [WorkerState.EXECUTING],
        WorkerState.EXECUTING: [
            WorkerState.VERIFYING,
            WorkerState.BLOCKED,
            WorkerState.WAITING,
            WorkerState.FAILED,
        ],
        WorkerState.VERIFYING: [
            WorkerState.SELF_REVIEW,
            WorkerState.FAILED,
        ],
        WorkerState.SELF_REVIEW: [
            WorkerState.COMPLETE,
            WorkerState.EXECUTING,  # Revision needed
        ],
        WorkerState.BLOCKED: [WorkerState.EXECUTING],
        WorkerState.WAITING: [WorkerState.IDLE],  # Fresh worker takes over
        WorkerState.COMPLETE: [WorkerState.IDLE],
        WorkerState.FAILED: [WorkerState.IDLE],
    }

    def __init__(self, worker_id: str):
        """Initialize worker protocol.

        Args:
            worker_id: Unique identifier for this worker
        """
        self.worker_id = worker_id
        self.state = WorkerState.IDLE
        self.current_task: str | None = None

    def transition(self, new_state: WorkerState) -> bool:
        """Attempt state transition.

        Args:
            new_state: Target state

        Returns:
            True if transition succeeded, False otherwise
        """
        valid_targets = self.VALID_TRANSITIONS.get(self.state, [])
        if new_state in valid_targets:
            self.state = new_state
            return True
        return False

    def can_accept_task(self) -> bool:
        """Check if worker can receive new task.

        Returns:
            True if worker is idle and can accept work
        """
        return self.state == WorkerState.IDLE


def check_context_threshold(context_usage: float) -> bool:
    """Check if worker should checkpoint and exit.

    Args:
        context_usage: Current context usage as ratio (0.0 - 1.0)

    Returns:
        True if context usage exceeds threshold
    """
    return context_usage >= CONTEXT_THRESHOLD


def create_checkpoint_signal(
    task_id: str,
    worker_id: str,
    current_step: int,
    files_created: list[str],
    files_modified: list[str],
) -> Message:
    """Create context threshold message with checkpoint data.

    Args:
        task_id: Current task identifier
        worker_id: Worker identifier
        current_step: Current execution step
        files_created: List of files created so far
        files_modified: List of files modified so far

    Returns:
        Message with checkpoint payload
    """
    return Message(
        type=MessageType.CONTEXT_THRESHOLD,
        worker_id=worker_id,
        timestamp=datetime.now(),
        payload={
            "task_id": task_id,
            "current_step": current_step,
            "files_created": files_created,
            "files_modified": files_modified,
            "checkpoint_ready": True,
        },
    )
