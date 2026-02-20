"""MAHABHARATHA v2 Messages - Message type definitions for worker communication."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MessageType(Enum):
    """Types of messages in the worker protocol."""

    ASSIGN = "assign"  # Orchestrator -> Worker: assign task
    HEARTBEAT = "heartbeat"  # Worker -> Orchestrator: I'm alive
    PROGRESS = "progress"  # Worker -> Orchestrator: status update
    COMPLETE = "complete"  # Worker -> Orchestrator: task done
    FAILED = "failed"  # Worker -> Orchestrator: task failed
    BLOCKED = "blocked"  # Worker -> Orchestrator: need help
    CONTEXT_THRESHOLD = "context_threshold"  # Worker -> Orchestrator: 70% context


@dataclass
class Message:
    """Base message structure."""

    type: MessageType
    worker_id: str
    timestamp: datetime
    payload: dict


@dataclass
class AssignMessage(Message):
    """Task assignment from orchestrator."""

    task_id: str
    spec_path: str
    worktree_path: str
    timeout_seconds: int


@dataclass
class HeartbeatMessage(Message):
    """Worker health check."""

    context_usage: float  # 0.0 - 1.0
    current_step: str | None


@dataclass
class ProgressMessage(Message):
    """Task progress update."""

    task_id: str
    step: int
    total_steps: int
    description: str


@dataclass
class CompleteMessage(Message):
    """Task completion report."""

    task_id: str
    files_created: list[str]
    files_modified: list[str]
    verification_passed: bool
    verification_output: str


@dataclass
class FailedMessage(Message):
    """Task failure report."""

    task_id: str
    error: str
    recoverable: bool
    checkpoint_path: str | None


@dataclass
class BlockedMessage(Message):
    """Worker blocked report."""

    task_id: str
    reason: str
    blocking_task_id: str | None
