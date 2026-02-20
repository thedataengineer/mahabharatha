"""Tests for MAHABHARATHA v2 Worktree Manager."""

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from worktree import MergeResult, Worktree, WorktreeManager


@pytest.fixture
def git_repo(tmp_path):
    """Create a test git repo."""
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=tmp_path, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        capture_output=True,
    )
    # Create initial commit
    (tmp_path / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial"], cwd=tmp_path, capture_output=True
    )
    return tmp_path


class TestWorktreeDataclass:
    """Tests for Worktree dataclass."""

    def test_worktree_creation(self, tmp_path):
        """Test Worktree can be created."""
        from datetime import datetime

        wt = Worktree(
            path=tmp_path / "test",
            branch="test-branch",
            worker_id="w1",
            created_at=datetime.now(),
        )
        assert wt.worker_id == "w1"
        assert wt.branch == "test-branch"


class TestMergeResult:
    """Tests for MergeResult dataclass."""

    def test_merge_result_success(self):
        """Test successful merge result."""
        result = MergeResult(success=True, conflicts=[])
        assert result.success
        assert result.conflicts == []

    def test_merge_result_conflict(self):
        """Test merge result with conflicts."""
        result = MergeResult(success=False, conflicts=["file1.py", "file2.py"])
        assert not result.success
        assert "file1.py" in result.conflicts


class TestWorktreeManager:
    """Tests for WorktreeManager class."""

    def test_manager_initialization(self, git_repo):
        """Test manager initializes correctly."""
        wm = WorktreeManager(git_repo)
        assert wm.repo_root == git_repo
        assert wm.worktrees == {}

    def test_create_worktree(self, git_repo):
        """Test creating a worktree."""
        wm = WorktreeManager(git_repo)
        wt = wm.create("w1")

        assert wt.path.exists()
        assert wt.branch == "mahabharatha/worker-w1"
        assert wt.worker_id == "w1"
        assert "w1" in wm.worktrees

    def test_create_multiple_worktrees(self, git_repo):
        """Test creating multiple worktrees."""
        wm = WorktreeManager(git_repo)
        wt1 = wm.create("w1")
        wt2 = wm.create("w2")

        assert wt1.path.exists()
        assert wt2.path.exists()
        assert wt1.path != wt2.path
        assert len(wm.worktrees) == 2

    def test_cleanup_worktree(self, git_repo):
        """Test cleaning up a worktree."""
        wm = WorktreeManager(git_repo)
        wt = wm.create("w1")
        path = wt.path

        wm.cleanup("w1")

        assert not path.exists()
        assert "w1" not in wm.worktrees

    def test_cleanup_nonexistent_worktree(self, git_repo):
        """Test cleanup of nonexistent worktree doesn't raise."""
        wm = WorktreeManager(git_repo)
        # Should not raise
        wm.cleanup("nonexistent")

    def test_worktree_path_structure(self, git_repo):
        """Test worktree path follows expected structure."""
        wm = WorktreeManager(git_repo)
        wt = wm.create("test-001")

        assert ".mahabharatha/worktrees/worker-test-001" in str(wt.path)


class TestWorktreeMerge:
    """Tests for worktree merge operations."""

    def test_merge_no_conflicts(self, git_repo):
        """Test merging worker branch with no conflicts."""
        wm = WorktreeManager(git_repo)
        wt = wm.create("w1")

        # Create a file in worktree
        (wt.path / "test.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=wt.path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add test"], cwd=wt.path, capture_output=True
        )

        # Merge back
        result = wm.merge_to_base("w1")
        assert result.success
        assert result.conflicts == []

    def test_merge_nonexistent_worker(self, git_repo):
        """Test merge fails for nonexistent worker."""
        wm = WorktreeManager(git_repo)
        with pytest.raises(ValueError, match="No worktree"):
            wm.merge_to_base("nonexistent")


class TestLevelMerge:
    """Tests for level-based merge operations."""

    def test_merge_level_branches(self, git_repo):
        """Test merging all branches for a level."""
        wm = WorktreeManager(git_repo)

        # Create two workers
        wt1 = wm.create("w1")
        wt2 = wm.create("w2")

        # Each creates a different file
        (wt1.path / "file1.txt").write_text("from w1")
        subprocess.run(["git", "add", "."], cwd=wt1.path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "W1 work"], cwd=wt1.path, capture_output=True
        )

        (wt2.path / "file2.txt").write_text("from w2")
        subprocess.run(["git", "add", "."], cwd=wt2.path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "W2 work"], cwd=wt2.path, capture_output=True
        )

        # Merge level
        result = wm.merge_level_branches(0, ["w1", "w2"])
        assert result.success
        assert result.merged_count == 2


class TestGitIntegration:
    """Tests for git integration."""

    def test_git_worktree_list(self, git_repo):
        """Test git recognizes created worktree."""
        wm = WorktreeManager(git_repo)
        wm.create("test-001")

        result = subprocess.run(
            ["git", "worktree", "list"], cwd=git_repo, capture_output=True, text=True
        )
        assert "worker-test-001" in result.stdout

    def test_branch_created_from_base(self, git_repo):
        """Test branch is created from specified base."""
        wm = WorktreeManager(git_repo)
        wm.create("w1", base_branch="main")

        result = subprocess.run(
            ["git", "branch", "-l"], cwd=git_repo, capture_output=True, text=True
        )
        assert "mahabharatha/worker-w1" in result.stdout
