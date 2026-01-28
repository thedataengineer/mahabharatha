"""Comprehensive tests for ZERG git_ops module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from zerg.exceptions import GitError, MergeConflictError
from zerg.git_ops import BranchInfo, GitOps


class TestGitOpsInit:
    """Tests for GitOps initialization."""

    def test_init_with_valid_repo(self, tmp_repo: Path) -> None:
        """Test initialization with a valid git repository."""
        ops = GitOps(tmp_repo)
        assert ops.repo_path == tmp_repo

    def test_init_with_string_path(self, tmp_repo: Path) -> None:
        """Test initialization with string path."""
        ops = GitOps(str(tmp_repo))
        assert ops.repo_path == tmp_repo

    def test_init_with_invalid_repo(self, tmp_path: Path) -> None:
        """Test initialization with invalid repository raises GitError."""
        with pytest.raises(GitError) as exc_info:
            GitOps(tmp_path)
        assert "Not a git repository" in str(exc_info.value)
        assert str(tmp_path) in str(exc_info.value.details)

    def test_init_with_worktree(self, tmp_repo: Path, tmp_path: Path) -> None:
        """Test initialization with a git worktree."""
        # Create worktree
        worktree_path = tmp_path / "worktree"
        subprocess.run(
            ["git", "-C", str(tmp_repo), "worktree", "add", str(worktree_path), "HEAD"],
            capture_output=True,
            check=True,
        )

        # .git is a file in worktrees, not a directory
        ops = GitOps(worktree_path)
        assert ops.repo_path == worktree_path


class TestGitOpsRun:
    """Tests for GitOps._run method."""

    def test_run_successful_command(self, tmp_repo: Path) -> None:
        """Test running a successful git command."""
        ops = GitOps(tmp_repo)
        result = ops._run("status")
        assert result.returncode == 0

    def test_run_failing_command_raises(self, tmp_repo: Path) -> None:
        """Test running a failing git command raises GitError."""
        ops = GitOps(tmp_repo)
        with pytest.raises(GitError) as exc_info:
            ops._run("checkout", "nonexistent-branch")
        assert exc_info.value.exit_code is not None

    def test_run_failing_command_no_check(self, tmp_repo: Path) -> None:
        """Test running a failing command with check=False."""
        ops = GitOps(tmp_repo)
        result = ops._run("checkout", "nonexistent-branch", check=False)
        assert result.returncode != 0

    def test_run_without_capture(self, tmp_repo: Path) -> None:
        """Test running command without capturing output."""
        ops = GitOps(tmp_repo)
        result = ops._run("status", capture=False)
        assert result.returncode == 0


class TestGitOpsBranch:
    """Tests for GitOps branch operations."""

    def test_current_branch(self, tmp_repo: Path) -> None:
        """Test getting current branch name."""
        ops = GitOps(tmp_repo)
        branch = ops.current_branch()
        assert isinstance(branch, str)
        assert branch  # Not empty

    def test_current_commit(self, tmp_repo: Path) -> None:
        """Test getting current commit SHA."""
        ops = GitOps(tmp_repo)
        commit = ops.current_commit()
        assert isinstance(commit, str)
        assert len(commit) == 40  # Full SHA

    def test_branch_exists_true(self, tmp_repo: Path) -> None:
        """Test branch_exists returns True for existing branch."""
        ops = GitOps(tmp_repo)
        current = ops.current_branch()
        assert ops.branch_exists(current) is True

    def test_branch_exists_false(self, tmp_repo: Path) -> None:
        """Test branch_exists returns False for non-existing branch."""
        ops = GitOps(tmp_repo)
        assert ops.branch_exists("nonexistent-branch-xyz") is False

    def test_create_branch(self, tmp_repo: Path) -> None:
        """Test creating a new branch."""
        ops = GitOps(tmp_repo)
        commit = ops.create_branch("test-branch")
        assert ops.branch_exists("test-branch")
        assert len(commit) == 40

    def test_create_branch_from_base(self, tmp_repo: Path) -> None:
        """Test creating a branch from specific base."""
        ops = GitOps(tmp_repo)
        base_commit = ops.current_commit()
        ops.create_branch("base-branch", base=base_commit)
        assert ops.branch_exists("base-branch")

    def test_delete_branch(self, tmp_repo: Path) -> None:
        """Test deleting a branch."""
        ops = GitOps(tmp_repo)
        ops.create_branch("to-delete")
        assert ops.branch_exists("to-delete")

        ops.delete_branch("to-delete")
        assert not ops.branch_exists("to-delete")

    def test_delete_branch_force(self, tmp_repo: Path) -> None:
        """Test force deleting a branch."""
        ops = GitOps(tmp_repo)
        ops.create_branch("force-delete")

        ops.delete_branch("force-delete", force=True)
        assert not ops.branch_exists("force-delete")

    def test_checkout(self, tmp_repo: Path) -> None:
        """Test checking out a branch."""
        ops = GitOps(tmp_repo)
        ops.create_branch("checkout-test")

        ops.checkout("checkout-test")
        assert ops.current_branch() == "checkout-test"

    def test_get_commit(self, tmp_repo: Path) -> None:
        """Test getting commit SHA for reference."""
        ops = GitOps(tmp_repo)
        commit = ops.get_commit("HEAD")
        assert len(commit) == 40
        assert commit == ops.current_commit()

    def test_get_commit_for_branch(self, tmp_repo: Path) -> None:
        """Test getting commit for specific branch."""
        ops = GitOps(tmp_repo)
        ops.create_branch("commit-test")
        branch_commit = ops.get_commit("commit-test")
        assert len(branch_commit) == 40


class TestGitOpsChanges:
    """Tests for GitOps change detection."""

    def test_has_changes_clean(self, tmp_repo: Path) -> None:
        """Test has_changes returns False for clean repo."""
        ops = GitOps(tmp_repo)
        assert ops.has_changes() is False

    def test_has_changes_untracked(self, tmp_repo: Path) -> None:
        """Test has_changes returns True for untracked files."""
        ops = GitOps(tmp_repo)
        (tmp_repo / "new-file.txt").write_text("content")
        assert ops.has_changes() is True

    def test_has_changes_modified(self, tmp_repo: Path) -> None:
        """Test has_changes returns True for modified files."""
        ops = GitOps(tmp_repo)
        (tmp_repo / "README.md").write_text("modified")
        assert ops.has_changes() is True

    def test_has_conflicts_false(self, tmp_repo: Path) -> None:
        """Test has_conflicts returns False when no conflicts."""
        ops = GitOps(tmp_repo)
        assert ops.has_conflicts() is False

    def test_get_conflicting_files_empty(self, tmp_repo: Path) -> None:
        """Test get_conflicting_files returns empty list."""
        ops = GitOps(tmp_repo)
        assert ops.get_conflicting_files() == []


class TestGitOpsCommit:
    """Tests for GitOps commit operations."""

    def test_commit_basic(self, tmp_repo: Path) -> None:
        """Test basic commit."""
        ops = GitOps(tmp_repo)
        (tmp_repo / "test.txt").write_text("content")

        commit = ops.commit("Test commit", add_all=True)
        assert len(commit) == 40
        assert not ops.has_changes()

    def test_commit_without_add_all(self, tmp_repo: Path) -> None:
        """Test commit without add_all requires staged changes."""
        ops = GitOps(tmp_repo)
        (tmp_repo / "staged.txt").write_text("staged content")
        subprocess.run(
            ["git", "-C", str(tmp_repo), "add", "staged.txt"],
            capture_output=True,
            check=True,
        )

        commit = ops.commit("Staged commit")
        assert len(commit) == 40

    def test_commit_allow_empty(self, tmp_repo: Path) -> None:
        """Test creating empty commit."""
        ops = GitOps(tmp_repo)
        commit = ops.commit("Empty commit", allow_empty=True)
        assert len(commit) == 40


class TestGitOpsMerge:
    """Tests for GitOps merge operations."""

    def test_merge_basic(self, tmp_repo: Path) -> None:
        """Test basic merge."""
        ops = GitOps(tmp_repo)
        original = ops.current_branch()

        # Create feature branch with changes
        ops.create_branch("feature")
        ops.checkout("feature")
        (tmp_repo / "feature.txt").write_text("feature content")
        ops.commit("Add feature", add_all=True)

        # Merge back
        ops.checkout(original)
        commit = ops.merge("feature", message="Merge feature")
        assert len(commit) == 40

    def test_merge_fast_forward(self, tmp_repo: Path) -> None:
        """Test merge with fast-forward."""
        ops = GitOps(tmp_repo)
        original = ops.current_branch()

        # Create feature branch with changes
        ops.create_branch("ff-feature")
        ops.checkout("ff-feature")
        (tmp_repo / "ff.txt").write_text("ff content")
        ops.commit("Add ff", add_all=True)

        ops.checkout(original)
        commit = ops.merge("ff-feature", no_ff=False)
        assert len(commit) == 40

    def test_merge_conflict(self, tmp_repo: Path) -> None:
        """Test merge with conflict raises MergeConflictError."""
        ops = GitOps(tmp_repo)
        original = ops.current_branch()

        # Create conflicting changes
        ops.create_branch("conflict")
        ops.checkout("conflict")
        (tmp_repo / "README.md").write_text("conflict content")
        ops.commit("Conflict change", add_all=True)

        ops.checkout(original)
        (tmp_repo / "README.md").write_text("main content")
        ops.commit("Main change", add_all=True)

        with pytest.raises(MergeConflictError) as exc_info:
            ops.merge("conflict")

        assert exc_info.value.source_branch == "conflict"
        assert exc_info.value.target_branch == original
        assert "README.md" in exc_info.value.conflicting_files

    def test_abort_merge(self, tmp_repo: Path) -> None:
        """Test aborting a merge."""
        ops = GitOps(tmp_repo)
        # abort_merge should work even with no merge in progress
        ops.abort_merge()


class TestGitOpsRebase:
    """Tests for GitOps rebase operations."""

    def test_rebase_success(self, tmp_repo: Path) -> None:
        """Test successful rebase."""
        ops = GitOps(tmp_repo)
        original = ops.current_branch()

        # Create changes on main
        (tmp_repo / "main.txt").write_text("main content")
        ops.commit("Main change", add_all=True)

        # Create feature branch from before main change
        ops.checkout(original)
        ops.create_branch("rebase-feature")
        ops.checkout("rebase-feature")
        (tmp_repo / "feature.txt").write_text("feature content")
        ops.commit("Feature change", add_all=True)

        # Rebase onto main
        ops.rebase(original)

    def test_rebase_conflict(self, tmp_repo: Path) -> None:
        """Test rebase with conflict raises MergeConflictError."""
        ops = GitOps(tmp_repo)
        original = ops.current_branch()

        # Create feature branch first
        ops.create_branch("rebase-conflict")
        ops.checkout("rebase-conflict")
        (tmp_repo / "README.md").write_text("feature version")
        ops.commit("Feature README", add_all=True)

        # Go back and make conflicting change on original
        ops.checkout(original)
        (tmp_repo / "README.md").write_text("main version")
        ops.commit("Main README", add_all=True)

        # Try to rebase feature onto main
        ops.checkout("rebase-conflict")
        with pytest.raises(MergeConflictError):
            ops.rebase(original)

    def test_abort_rebase(self, tmp_repo: Path) -> None:
        """Test aborting a rebase."""
        ops = GitOps(tmp_repo)
        ops.abort_rebase()


class TestGitOpsStagingBranch:
    """Tests for GitOps staging branch operations."""

    def test_create_staging_branch(self, tmp_repo: Path) -> None:
        """Test creating staging branch."""
        ops = GitOps(tmp_repo)
        base = ops.current_branch()

        staging = ops.create_staging_branch("test-feature", base=base)
        assert staging == "zerg/test-feature/staging"
        assert ops.branch_exists(staging)

    def test_create_staging_branch_overwrites(self, tmp_repo: Path) -> None:
        """Test creating staging branch overwrites existing."""
        ops = GitOps(tmp_repo)
        base = ops.current_branch()

        # Create first time
        ops.create_staging_branch("overwrite-feature", base=base)
        first_commit = ops.get_commit("zerg/overwrite-feature/staging")

        # Make a new commit
        (tmp_repo / "new.txt").write_text("new")
        ops.commit("New commit", add_all=True)

        # Create again (should be at new commit)
        ops.create_staging_branch("overwrite-feature", base=base)
        second_commit = ops.get_commit("zerg/overwrite-feature/staging")

        # Should have been recreated from current HEAD
        assert first_commit != second_commit


class TestGitOpsListBranches:
    """Tests for GitOps branch listing."""

    def test_list_branches(self, tmp_repo: Path) -> None:
        """Test listing all branches."""
        ops = GitOps(tmp_repo)
        ops.create_branch("list-test-1")
        ops.create_branch("list-test-2")

        branches = ops.list_branches()
        assert isinstance(branches, list)
        assert all(isinstance(b, BranchInfo) for b in branches)
        assert len(branches) >= 3  # Original + 2 new

    def test_list_branches_with_pattern(self, tmp_repo: Path) -> None:
        """Test listing branches with pattern."""
        ops = GitOps(tmp_repo)
        ops.create_branch("zerg/feat/worker-0")
        ops.create_branch("zerg/feat/worker-1")
        ops.create_branch("other-branch")

        branches = ops.list_branches("zerg/feat/worker-*")
        assert len(branches) == 2
        assert all("worker-" in b.name for b in branches)

    def test_list_branches_empty_result(self, tmp_repo: Path) -> None:
        """Test listing branches with no matches."""
        ops = GitOps(tmp_repo)
        branches = ops.list_branches("nonexistent-pattern-*")
        assert branches == []

    def test_list_branches_current_indicator(self, tmp_repo: Path) -> None:
        """Test that current branch is marked."""
        ops = GitOps(tmp_repo)
        current = ops.current_branch()

        branches = ops.list_branches()
        current_branches = [b for b in branches if b.is_current]
        assert len(current_branches) == 1
        assert current_branches[0].name == current

    def test_list_worker_branches(self, tmp_repo: Path) -> None:
        """Test listing worker branches for feature."""
        ops = GitOps(tmp_repo)
        ops.create_branch("zerg/myfeature/worker-0")
        ops.create_branch("zerg/myfeature/worker-1")
        ops.create_branch("zerg/other/worker-0")

        workers = ops.list_worker_branches("myfeature")
        assert len(workers) == 2
        assert "zerg/myfeature/worker-0" in workers
        assert "zerg/myfeature/worker-1" in workers


class TestGitOpsDeleteFeatureBranches:
    """Tests for GitOps feature branch deletion."""

    def test_delete_feature_branches(self, tmp_repo: Path) -> None:
        """Test deleting all feature branches."""
        ops = GitOps(tmp_repo)
        ops.create_branch("zerg/cleanup/worker-0")
        ops.create_branch("zerg/cleanup/worker-1")
        ops.create_branch("zerg/cleanup/staging")

        count = ops.delete_feature_branches("cleanup")
        assert count == 3
        assert not ops.branch_exists("zerg/cleanup/worker-0")
        assert not ops.branch_exists("zerg/cleanup/worker-1")
        assert not ops.branch_exists("zerg/cleanup/staging")

    def test_delete_feature_branches_skips_current(self, tmp_repo: Path) -> None:
        """Test that current branch is not deleted."""
        ops = GitOps(tmp_repo)
        ops.create_branch("zerg/skip/worker-0")
        ops.checkout("zerg/skip/worker-0")
        ops.create_branch("zerg/skip/worker-1")

        count = ops.delete_feature_branches("skip")
        assert count == 1  # Only worker-1 deleted
        assert ops.branch_exists("zerg/skip/worker-0")  # Still exists (current)


class TestGitOpsFetchPush:
    """Tests for GitOps fetch and push operations."""

    def test_fetch_basic(self, tmp_repo: Path) -> None:
        """Test fetch from remote (mocked)."""
        ops = GitOps(tmp_repo)

        # Add a remote
        subprocess.run(
            ["git", "-C", str(tmp_repo), "remote", "add", "origin", str(tmp_repo)],
            capture_output=True,
        )

        # This should not raise
        ops.fetch()

    def test_fetch_specific_branch(self, tmp_repo: Path) -> None:
        """Test fetch specific branch (mocked)."""
        ops = GitOps(tmp_repo)

        subprocess.run(
            ["git", "-C", str(tmp_repo), "remote", "add", "origin", str(tmp_repo)],
            capture_output=True,
        )

        # Fetch specific branch
        current = ops.current_branch()
        ops.fetch("origin", current)

    def test_push_args(self, tmp_repo: Path) -> None:
        """Test push command builds correct arguments."""
        ops = GitOps(tmp_repo)

        with patch.object(ops, "_run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            ops.push("origin", "main", force=True, set_upstream=True)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0]
            assert "push" in call_args
            assert "origin" in call_args
            assert "main" in call_args
            assert "--force" in call_args
            assert "--set-upstream" in call_args


class TestGitOpsStash:
    """Tests for GitOps stash operations."""

    def test_stash_with_changes(self, tmp_repo: Path) -> None:
        """Test stashing changes."""
        ops = GitOps(tmp_repo)
        (tmp_repo / "README.md").write_text("modified content")

        stashed = ops.stash("Test stash")
        assert stashed is True
        assert (tmp_repo / "README.md").read_text() == "# Test Repo"

    def test_stash_no_changes(self, tmp_repo: Path) -> None:
        """Test stash with no changes returns False."""
        ops = GitOps(tmp_repo)
        stashed = ops.stash()
        assert stashed is False

    def test_stash_without_message(self, tmp_repo: Path) -> None:
        """Test stash without message."""
        ops = GitOps(tmp_repo)
        (tmp_repo / "README.md").write_text("modified")
        stashed = ops.stash()
        assert stashed is True

    def test_stash_pop(self, tmp_repo: Path) -> None:
        """Test popping stash."""
        ops = GitOps(tmp_repo)
        (tmp_repo / "README.md").write_text("pop test content")
        ops.stash("Pop test")

        ops.stash_pop()
        assert (tmp_repo / "README.md").read_text() == "pop test content"


class TestBranchInfo:
    """Tests for BranchInfo dataclass."""

    def test_create_full(self) -> None:
        """Test creating BranchInfo with all fields."""
        info = BranchInfo(
            name="test-branch",
            commit="abc123def456",
            is_current=True,
            upstream="origin/test-branch",
        )
        assert info.name == "test-branch"
        assert info.commit == "abc123def456"
        assert info.is_current is True
        assert info.upstream == "origin/test-branch"

    def test_create_minimal(self) -> None:
        """Test creating BranchInfo with minimal fields."""
        info = BranchInfo(name="test", commit="abc123")
        assert info.name == "test"
        assert info.commit == "abc123"
        assert info.is_current is False
        assert info.upstream is None


class TestGitOpsErrorHandling:
    """Tests for GitOps error handling."""

    def test_run_captures_stderr(self, tmp_repo: Path) -> None:
        """Test that GitError includes stderr information."""
        ops = GitOps(tmp_repo)
        with pytest.raises(GitError) as exc_info:
            ops._run("checkout", "nonexistent-xyz")

        # Error message should include stderr content
        assert exc_info.value.command is not None
        assert "git" in exc_info.value.command

    def test_merge_git_error_without_conflict(self, tmp_repo: Path) -> None:
        """Test merge raises GitError for non-conflict errors."""
        ops = GitOps(tmp_repo)

        with pytest.raises(GitError):
            ops.merge("nonexistent-branch")

    def test_rebase_git_error_without_conflict(self, tmp_repo: Path) -> None:
        """Test rebase raises GitError for non-conflict errors."""
        ops = GitOps(tmp_repo)

        with pytest.raises(GitError):
            ops.rebase("nonexistent-branch")
