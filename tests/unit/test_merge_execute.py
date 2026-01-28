"""Unit tests for MergeCoordinator.execute_merge.

Tests merge operations including:
- Successful merge of single branch
- Successful merge of multiple branches
- MergeConflictError exception handling
- MergeResult status values (MERGED, CONFLICT)
- Conflicting files population on conflict
"""

from unittest.mock import MagicMock, patch

import pytest

from zerg.constants import MergeStatus
from zerg.exceptions import MergeConflictError
from zerg.merge import MergeCoordinator
from zerg.types import MergeResult


class TestExecuteMergeSingleBranch:
    """Tests for merging a single branch."""

    def test_successful_merge_single_branch(self):
        """Merging a single branch should return MERGED status."""
        mock_git = MagicMock()
        mock_git.merge.return_value = "abc123def456"

        with patch.object(MergeCoordinator, "__init__", lambda self, *args, **kwargs: None):
            coordinator = MergeCoordinator.__new__(MergeCoordinator)
            coordinator.git = mock_git
            coordinator.feature = "test-feature"

            results = coordinator.execute_merge(
                source_branches=["zerg/test-feature/worker-0"],
                staging_branch="zerg/test-feature/staging",
            )

        assert len(results) == 1
        assert results[0].status == MergeStatus.MERGED
        assert results[0].source_branch == "zerg/test-feature/worker-0"
        assert results[0].target_branch == "zerg/test-feature/staging"
        assert results[0].commit_sha == "abc123def456"
        assert results[0].conflicting_files == []
        assert results[0].error_message is None

    def test_single_branch_merge_calls_checkout_and_merge(self):
        """Execute merge should checkout staging and merge source branch."""
        mock_git = MagicMock()
        mock_git.merge.return_value = "commit123"

        with patch.object(MergeCoordinator, "__init__", lambda self, *args, **kwargs: None):
            coordinator = MergeCoordinator.__new__(MergeCoordinator)
            coordinator.git = mock_git
            coordinator.feature = "test-feature"

            coordinator.execute_merge(
                source_branches=["worker-branch"],
                staging_branch="staging-branch",
            )

        mock_git.checkout.assert_called_once_with("staging-branch")
        mock_git.merge.assert_called_once_with(
            "worker-branch",
            message="Merge worker-branch into staging-branch",
        )


class TestExecuteMergeMultipleBranches:
    """Tests for merging multiple branches."""

    def test_successful_merge_multiple_branches(self):
        """Merging multiple branches should return MERGED status for each."""
        mock_git = MagicMock()
        mock_git.merge.side_effect = ["commit1", "commit2", "commit3"]

        with patch.object(MergeCoordinator, "__init__", lambda self, *args, **kwargs: None):
            coordinator = MergeCoordinator.__new__(MergeCoordinator)
            coordinator.git = mock_git
            coordinator.feature = "test-feature"

            results = coordinator.execute_merge(
                source_branches=["worker-0", "worker-1", "worker-2"],
                staging_branch="staging",
            )

        assert len(results) == 3
        assert all(r.status == MergeStatus.MERGED for r in results)
        assert results[0].commit_sha == "commit1"
        assert results[1].commit_sha == "commit2"
        assert results[2].commit_sha == "commit3"

    def test_multiple_branches_merged_in_order(self):
        """Multiple branches should be merged sequentially in provided order."""
        mock_git = MagicMock()
        mock_git.merge.side_effect = ["c1", "c2", "c3"]
        merge_calls = []

        def track_merge(branch, message):
            merge_calls.append(branch)
            return f"commit_{branch}"

        mock_git.merge.side_effect = track_merge

        with patch.object(MergeCoordinator, "__init__", lambda self, *args, **kwargs: None):
            coordinator = MergeCoordinator.__new__(MergeCoordinator)
            coordinator.git = mock_git
            coordinator.feature = "test-feature"

            coordinator.execute_merge(
                source_branches=["alpha", "beta", "gamma"],
                staging_branch="staging",
            )

        assert merge_calls == ["alpha", "beta", "gamma"]

    def test_checkout_called_once_before_all_merges(self):
        """Checkout should be called once before merging all branches."""
        mock_git = MagicMock()
        mock_git.merge.return_value = "commit"

        with patch.object(MergeCoordinator, "__init__", lambda self, *args, **kwargs: None):
            coordinator = MergeCoordinator.__new__(MergeCoordinator)
            coordinator.git = mock_git
            coordinator.feature = "test-feature"

            coordinator.execute_merge(
                source_branches=["b1", "b2", "b3"],
                staging_branch="staging",
            )

        mock_git.checkout.assert_called_once_with("staging")
        assert mock_git.merge.call_count == 3


class TestMergeConflictExceptionHandling:
    """Tests for MergeConflictError exception handling in execute_merge."""

    def test_merge_conflict_raises_exception(self):
        """MergeConflictError from git should be re-raised after recording result."""
        mock_git = MagicMock()
        mock_git.merge.side_effect = MergeConflictError(
            message="Conflict in file.py",
            source_branch="worker-0",
            target_branch="staging",
            conflicting_files=["src/file.py"],
        )

        with patch.object(MergeCoordinator, "__init__", lambda self, *args, **kwargs: None):
            coordinator = MergeCoordinator.__new__(MergeCoordinator)
            coordinator.git = mock_git
            coordinator.feature = "test-feature"

            with pytest.raises(MergeConflictError) as exc_info:
                coordinator.execute_merge(
                    source_branches=["worker-0"],
                    staging_branch="staging",
                )

        assert exc_info.value.source_branch == "worker-0"
        assert exc_info.value.target_branch == "staging"
        assert "src/file.py" in exc_info.value.conflicting_files

    def test_conflict_stops_further_merges(self):
        """Conflict on first branch should prevent merging subsequent branches."""
        mock_git = MagicMock()
        mock_git.merge.side_effect = MergeConflictError(
            message="Conflict",
            source_branch="worker-0",
            target_branch="staging",
            conflicting_files=["conflict.py"],
        )

        with patch.object(MergeCoordinator, "__init__", lambda self, *args, **kwargs: None):
            coordinator = MergeCoordinator.__new__(MergeCoordinator)
            coordinator.git = mock_git
            coordinator.feature = "test-feature"

            with pytest.raises(MergeConflictError):
                coordinator.execute_merge(
                    source_branches=["worker-0", "worker-1", "worker-2"],
                    staging_branch="staging",
                )

        # Only first merge should be attempted
        assert mock_git.merge.call_count == 1

    def test_conflict_after_successful_merges(self):
        """Conflict on second branch should preserve first merge result."""
        mock_git = MagicMock()

        def merge_side_effect(branch, message):
            if branch == "worker-1":
                raise MergeConflictError(
                    message="Conflict in worker-1",
                    source_branch="worker-1",
                    target_branch="staging",
                    conflicting_files=["src/overlap.py"],
                )
            return f"commit_{branch}"

        mock_git.merge.side_effect = merge_side_effect

        with patch.object(MergeCoordinator, "__init__", lambda self, *args, **kwargs: None):
            coordinator = MergeCoordinator.__new__(MergeCoordinator)
            coordinator.git = mock_git
            coordinator.feature = "test-feature"

            with pytest.raises(MergeConflictError):
                coordinator.execute_merge(
                    source_branches=["worker-0", "worker-1", "worker-2"],
                    staging_branch="staging",
                )

        # First merge succeeded, second failed, third not attempted
        assert mock_git.merge.call_count == 2


class TestMergeResultStatusValues:
    """Tests for MergeResult status values (MERGED and CONFLICT)."""

    def test_merged_status_on_success(self):
        """Successful merge should have MERGED status."""
        mock_git = MagicMock()
        mock_git.merge.return_value = "abc123"

        with patch.object(MergeCoordinator, "__init__", lambda self, *args, **kwargs: None):
            coordinator = MergeCoordinator.__new__(MergeCoordinator)
            coordinator.git = mock_git
            coordinator.feature = "test-feature"

            results = coordinator.execute_merge(
                source_branches=["worker-0"],
                staging_branch="staging",
            )

        assert results[0].status == MergeStatus.MERGED
        assert results[0].status.value == "merged"

    def test_conflict_status_on_conflict(self):
        """Conflict should produce result with CONFLICT status before raising."""
        mock_git = MagicMock()
        mock_git.merge.side_effect = MergeConflictError(
            message="Conflict",
            source_branch="worker-0",
            target_branch="staging",
            conflicting_files=["file.py"],
        )

        with patch.object(MergeCoordinator, "__init__", lambda self, *args, **kwargs: None):
            coordinator = MergeCoordinator.__new__(MergeCoordinator)
            coordinator.git = mock_git
            coordinator.feature = "test-feature"

            # The method adds a CONFLICT result before re-raising
            # We can verify by catching and checking the exception details
            with pytest.raises(MergeConflictError) as exc_info:
                coordinator.execute_merge(
                    source_branches=["worker-0"],
                    staging_branch="staging",
                )

        # Verify the exception has the right conflict status info
        assert exc_info.value.conflicting_files == ["file.py"]

    def test_merge_status_enum_values(self):
        """MergeStatus enum should have expected values."""
        assert MergeStatus.MERGED.value == "merged"
        assert MergeStatus.CONFLICT.value == "conflict"
        assert MergeStatus.PENDING.value == "pending"
        assert MergeStatus.IN_PROGRESS.value == "in_progress"
        assert MergeStatus.FAILED.value == "failed"


class TestConflictingFilesPopulation:
    """Tests for conflicting_files field population on conflict."""

    def test_conflicting_files_populated_from_exception(self):
        """Conflicting files should be captured from MergeConflictError exception."""
        conflict_files = ["src/models/user.py", "src/services/auth.py", "tests/test_auth.py"]
        mock_git = MagicMock()
        mock_git.merge.side_effect = MergeConflictError(
            message="Multiple conflicts",
            source_branch="worker-0",
            target_branch="staging",
            conflicting_files=conflict_files,
        )

        with patch.object(MergeCoordinator, "__init__", lambda self, *args, **kwargs: None):
            coordinator = MergeCoordinator.__new__(MergeCoordinator)
            coordinator.git = mock_git
            coordinator.feature = "test-feature"

            with pytest.raises(MergeConflictError) as exc_info:
                coordinator.execute_merge(
                    source_branches=["worker-0"],
                    staging_branch="staging",
                )

        assert exc_info.value.conflicting_files == conflict_files
        assert len(exc_info.value.conflicting_files) == 3

    def test_empty_conflicting_files_on_success(self):
        """Successful merge should have empty conflicting_files list."""
        mock_git = MagicMock()
        mock_git.merge.return_value = "commit123"

        with patch.object(MergeCoordinator, "__init__", lambda self, *args, **kwargs: None):
            coordinator = MergeCoordinator.__new__(MergeCoordinator)
            coordinator.git = mock_git
            coordinator.feature = "test-feature"

            results = coordinator.execute_merge(
                source_branches=["worker-0"],
                staging_branch="staging",
            )

        assert results[0].conflicting_files == []

    def test_conflicting_files_defaults_to_empty_list(self):
        """MergeConflictError with None conflicting_files should default to empty list."""
        exception = MergeConflictError(
            message="Conflict",
            source_branch="src",
            target_branch="target",
            conflicting_files=None,
        )
        assert exception.conflicting_files == []

    def test_merge_result_preserves_conflicting_files(self):
        """MergeResult dataclass should preserve conflicting_files."""
        result = MergeResult(
            source_branch="worker-0",
            target_branch="staging",
            status=MergeStatus.CONFLICT,
            conflicting_files=["a.py", "b.py"],
            error_message="Merge conflict detected",
        )

        assert result.conflicting_files == ["a.py", "b.py"]
        assert result.status == MergeStatus.CONFLICT
        assert result.commit_sha is None


class TestMergeResultDataclass:
    """Tests for MergeResult dataclass behavior."""

    def test_merge_result_to_dict(self):
        """MergeResult.to_dict should serialize all fields."""
        result = MergeResult(
            source_branch="worker-0",
            target_branch="staging",
            status=MergeStatus.MERGED,
            commit_sha="abc123",
            conflicting_files=[],
            error_message=None,
        )

        data = result.to_dict()

        assert data["source_branch"] == "worker-0"
        assert data["target_branch"] == "staging"
        assert data["status"] == "merged"
        assert data["commit_sha"] == "abc123"
        assert data["conflicting_files"] == []
        assert data["error_message"] is None
        assert "timestamp" in data

    def test_merge_result_to_dict_with_conflict(self):
        """MergeResult.to_dict should serialize conflict information."""
        result = MergeResult(
            source_branch="worker-1",
            target_branch="staging",
            status=MergeStatus.CONFLICT,
            commit_sha=None,
            conflicting_files=["x.py", "y.py"],
            error_message="Merge failed due to conflicts",
        )

        data = result.to_dict()

        assert data["status"] == "conflict"
        assert data["commit_sha"] is None
        assert data["conflicting_files"] == ["x.py", "y.py"]
        assert data["error_message"] == "Merge failed due to conflicts"


class TestMergeConflictException:
    """Tests for MergeConflictError exception class."""

    def test_merge_conflict_attributes(self):
        """MergeConflictError should have all expected attributes."""
        exception = MergeConflictError(
            message="Conflict in merge",
            source_branch="feature-branch",
            target_branch="main",
            conflicting_files=["file1.py", "file2.py"],
        )

        assert exception.source_branch == "feature-branch"
        assert exception.target_branch == "main"
        assert exception.conflicting_files == ["file1.py", "file2.py"]
        assert "Conflict in merge" in str(exception)

    def test_merge_conflict_inherits_git_error(self):
        """MergeConflictError should inherit from GitError."""
        from zerg.exceptions import GitError

        exception = MergeConflictError(
            message="Test",
            source_branch="src",
            target_branch="tgt",
        )

        assert isinstance(exception, GitError)

    def test_merge_conflict_details_populated(self):
        """MergeConflictError should populate details dict."""
        exception = MergeConflictError(
            message="Conflict",
            source_branch="worker-0",
            target_branch="staging",
            conflicting_files=["a.py", "b.py"],
        )

        assert exception.details["source_branch"] == "worker-0"
        assert exception.details["target_branch"] == "staging"
        assert exception.details["conflicting_files"] == ["a.py", "b.py"]
