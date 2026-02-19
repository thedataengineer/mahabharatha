"""ZERG git package -- structured git operations.

Re-exports core classes for convenient access:
    from mahabharatha.git import GitOps, GitRunner, BranchInfo
"""

from mahabharatha.git.base import GitRunner
from mahabharatha.git.config import GitConfig, detect_context
from mahabharatha.git.ops import BranchInfo, GitOps
from mahabharatha.git.types import (
    CommitInfo,
    CommitType,
    DiffAnalysis,
    RescueSnapshot,
    ReviewFinding,
)

__all__ = [
    "GitRunner",
    "GitOps",
    "BranchInfo",
    "GitConfig",
    "detect_context",
    "CommitType",
    "CommitInfo",
    "DiffAnalysis",
    "ReviewFinding",
    "RescueSnapshot",
]
