"""MAHABHARATHA v2 Worktree Manager - Git worktree management for worker isolation."""

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Worktree:
    """Represents a git worktree."""

    path: Path
    branch: str
    worker_id: str
    created_at: datetime


@dataclass
class MergeResult:
    """Result of a merge operation."""

    success: bool
    conflicts: list[str]
    commit_sha: str | None = None


@dataclass
class LevelMergeResult:
    """Result of merging all branches for a level."""

    success: bool
    merged_count: int = 0
    failed_worker: str | None = None
    conflicts: list[str] | None = None


class WorktreeManager:
    """Manages git worktrees for worker isolation."""

    WORKTREE_DIR = ".mahabharatha/worktrees"
    BRANCH_PREFIX = "mahabharatha"

    def __init__(self, repo_root: Path | None = None):
        """Initialize worktree manager.

        Args:
            repo_root: Root of git repository. Defaults to current directory.
        """
        self.repo_root = repo_root or Path.cwd()
        self.worktrees: dict[str, Worktree] = {}

    def create(self, worker_id: str, base_branch: str = "main") -> Worktree:
        """Create worktree for worker.

        Creates:
        - Branch: mahabharatha/worker-{worker_id}
        - Worktree: .mahabharatha/worktrees/worker-{worker_id}

        Args:
            worker_id: Unique identifier for the worker
            base_branch: Branch to base the new branch on

        Returns:
            Worktree instance
        """
        branch_name = f"{self.BRANCH_PREFIX}/worker-{worker_id}"
        worktree_path = self.repo_root / self.WORKTREE_DIR / f"worker-{worker_id}"

        # Create branch from base
        self._run_git(["branch", branch_name, base_branch])

        # Create worktree
        worktree_path.parent.mkdir(parents=True, exist_ok=True)
        self._run_git(["worktree", "add", str(worktree_path), branch_name])

        wt = Worktree(
            path=worktree_path,
            branch=branch_name,
            worker_id=worker_id,
            created_at=datetime.now(),
        )
        self.worktrees[worker_id] = wt
        return wt

    def cleanup(self, worker_id: str) -> None:
        """Remove worktree and optionally delete branch.

        Args:
            worker_id: Worker ID to clean up
        """
        wt = self.worktrees.get(worker_id)
        if not wt:
            return

        # Remove worktree
        self._run_git(["worktree", "remove", str(wt.path), "--force"], check=False)

        # Prune worktree references
        self._run_git(["worktree", "prune"])

        del self.worktrees[worker_id]

    def merge_to_base(self, worker_id: str, base_branch: str = "main") -> MergeResult:
        """Merge worker branch back to base.

        Args:
            worker_id: Worker whose branch to merge
            base_branch: Branch to merge into

        Returns:
            MergeResult with success status and any conflicts

        Raises:
            ValueError: If no worktree exists for worker
        """
        wt = self.worktrees.get(worker_id)
        if not wt:
            raise ValueError(f"No worktree for worker {worker_id}")

        # Checkout base branch (in main repo)
        self._run_git(["checkout", base_branch])

        # Merge worker branch
        result = self._run_git(
            ["merge", "--no-ff", wt.branch, "-m", f"Merge {wt.branch}"], check=False
        )

        if result.returncode != 0:
            return MergeResult(success=False, conflicts=self._get_conflicts())

        # Get commit SHA
        sha_result = self._run_git(["rev-parse", "HEAD"])
        commit_sha = sha_result.stdout.strip()

        return MergeResult(success=True, conflicts=[], commit_sha=commit_sha)

    def merge_level_branches(
        self, level: int, worker_ids: list[str], base_branch: str = "main"
    ) -> LevelMergeResult:
        """Sequentially merge all worker branches for a level.

        Args:
            level: Level number (for logging)
            worker_ids: List of worker IDs to merge
            base_branch: Branch to merge into

        Returns:
            LevelMergeResult with overall status
        """
        merged_count = 0

        for worker_id in worker_ids:
            result = self.merge_to_base(worker_id, base_branch)

            if not result.success:
                # Stop on first conflict
                return LevelMergeResult(
                    success=False,
                    merged_count=merged_count,
                    failed_worker=worker_id,
                    conflicts=result.conflicts,
                )

            merged_count += 1

        return LevelMergeResult(success=True, merged_count=merged_count)

    def _run_git(
        self, args: list[str], check: bool = True
    ) -> subprocess.CompletedProcess:
        """Execute git command.

        Args:
            args: Git command arguments
            check: Whether to raise on non-zero exit

        Returns:
            CompletedProcess instance
        """
        return subprocess.run(
            ["git"] + args,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=check,
        )

    def _get_conflicts(self) -> list[str]:
        """Get list of conflicting files.

        Returns:
            List of file paths with conflicts
        """
        result = self._run_git(
            ["diff", "--name-only", "--diff-filter=U"], check=False
        )
        if result.stdout:
            return [f for f in result.stdout.strip().split("\n") if f]
        return []
