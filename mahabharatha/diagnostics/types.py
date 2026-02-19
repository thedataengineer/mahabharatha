"""Shared types and data models for the ZERG diagnostic system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "DiagnosticContext",
    "ErrorCategory",
    "ErrorFingerprint",
    "ErrorSeverity",
    "Evidence",
    "ScoredHypothesis",
    "TimelineEvent",
]


class ErrorSeverity(Enum):
    """Severity levels for diagnostic errors."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ErrorCategory(Enum):
    """Categories for classifying diagnostic errors."""

    WORKER_FAILURE = "worker_failure"
    TASK_FAILURE = "task_failure"
    STATE_CORRUPTION = "state_corruption"
    INFRASTRUCTURE = "infrastructure"
    CODE_ERROR = "code_error"
    DEPENDENCY = "dependency"
    MERGE_CONFLICT = "merge_conflict"
    ENVIRONMENT = "environment"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


@dataclass
class ErrorFingerprint:
    """Unique fingerprint for identifying and deduplicating errors."""

    hash: str
    language: str  # python/javascript/go/rust/java/cpp/unknown
    error_type: str
    message_template: str
    file: str
    line: int = 0
    column: int = 0
    function: str = ""
    module: str = ""
    chain: list[ErrorFingerprint] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hash": self.hash,
            "language": self.language,
            "error_type": self.error_type,
            "message_template": self.message_template,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "function": self.function,
            "module": self.module,
            "chain": [fp.to_dict() for fp in self.chain],
        }


@dataclass
class TimelineEvent:
    """A single event in the diagnostic timeline."""

    timestamp: str
    worker_id: int
    event_type: str  # error/warning/info/state_change
    message: str
    source_file: str = ""
    line_number: int = 0
    correlation_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "worker_id": self.worker_id,
            "event_type": self.event_type,
            "message": self.message,
            "source_file": self.source_file,
            "line_number": self.line_number,
            "correlation_id": self.correlation_id,
        }


@dataclass
class Evidence:
    """A piece of evidence supporting or contradicting a hypothesis."""

    description: str
    source: str  # log/state/git/system/code
    confidence: float  # 0.0-1.0
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "description": self.description,
            "source": self.source,
            "confidence": self.confidence,
            "data": self.data,
        }


@dataclass
class ScoredHypothesis:
    """A diagnostic hypothesis with Bayesian scoring."""

    description: str
    category: ErrorCategory
    prior_probability: float
    evidence_for: list[Evidence] = field(default_factory=list)
    evidence_against: list[Evidence] = field(default_factory=list)
    posterior_probability: float = 0.5
    test_command: str = ""
    test_result: str | None = None
    suggested_fix: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "description": self.description,
            "category": self.category.value,
            "prior_probability": self.prior_probability,
            "evidence_for": [e.to_dict() for e in self.evidence_for],
            "evidence_against": [e.to_dict() for e in self.evidence_against],
            "posterior_probability": self.posterior_probability,
            "test_command": self.test_command,
            "test_result": self.test_result,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class DiagnosticContext:
    """Context for a diagnostic session."""

    feature: str = ""
    worker_id: int | None = None
    error_text: str = ""
    stack_trace: str = ""
    deep: bool = False
    auto_fix: bool = False
    interactive: bool = False
    verbose: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "feature": self.feature,
            "worker_id": self.worker_id,
            "error_text": self.error_text,
            "stack_trace": self.stack_trace,
            "deep": self.deep,
            "auto_fix": self.auto_fix,
            "interactive": self.interactive,
            "verbose": self.verbose,
        }
