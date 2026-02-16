"""Tests for advisory lockfile functions in zerg.commands._utils."""

import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from zerg.commands._utils import acquire_feature_lock, check_feature_lock, release_feature_lock


class TestAcquireFeatureLock:
    """Tests for acquire_feature_lock()."""

    def test_acquires_lock_when_none_exists(self, tmp_path: Path) -> None:
        """Lock is acquired when no lock file exists; file is created."""
        gsd_dir = str(tmp_path)
        feature = "my-feature"

        result = acquire_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is True
        lock_path = tmp_path / "specs" / feature / ".lock"
        assert lock_path.exists()

        # Verify lock content format: "pid:timestamp"
        content = lock_path.read_text().strip()
        pid_str, ts_str = content.split(":", 1)
        assert int(pid_str) == os.getpid()
        assert float(ts_str) > 0

    def test_returns_false_when_active_lock_exists(self, tmp_path: Path) -> None:
        """Returns False when another session holds an active lock."""
        gsd_dir = str(tmp_path)
        feature = "locked-feature"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        # Write a recent lock from a different PID
        lock_path.write_text(f"99999:{time.time()}")

        result = acquire_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is False
        # Original lock should still be intact
        content = lock_path.read_text()
        assert content.startswith("99999:")

    def test_cleans_up_stale_lock_and_acquires(self, tmp_path: Path) -> None:
        """Stale lock (> 2 hours old) is cleaned up and new lock acquired."""
        gsd_dir = str(tmp_path)
        feature = "stale-feature"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        # Write a lock from 3 hours ago
        stale_timestamp = time.time() - 10800  # 3 hours ago
        lock_path.write_text(f"12345:{stale_timestamp}")

        result = acquire_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is True
        # Verify new lock was written with current PID
        content = lock_path.read_text().strip()
        pid_str, _ = content.split(":", 1)
        assert int(pid_str) == os.getpid()

    def test_cleans_up_corrupt_lock_and_acquires(self, tmp_path: Path) -> None:
        """Corrupt lock file is removed and new lock acquired."""
        gsd_dir = str(tmp_path)
        feature = "corrupt-feature"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        # Write garbage content
        lock_path.write_text("not-valid-lock-content")

        result = acquire_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is True
        content = lock_path.read_text().strip()
        pid_str, ts_str = content.split(":", 1)
        assert int(pid_str) == os.getpid()
        assert float(ts_str) > 0

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Lock acquisition creates parent directories if they do not exist."""
        gsd_dir = str(tmp_path)
        feature = "new-feature"

        # Verify the specs dir does not exist yet
        assert not (tmp_path / "specs" / feature).exists()

        result = acquire_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is True
        assert (tmp_path / "specs" / feature / ".lock").exists()

    def test_lock_just_at_boundary_is_still_active(self, tmp_path: Path) -> None:
        """A lock exactly at the 2-hour boundary is still considered active."""
        gsd_dir = str(tmp_path)
        feature = "boundary-feature"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        # Write a lock at exactly 7200 seconds ago (boundary)
        current_time = time.time()
        boundary_timestamp = current_time - 7200
        lock_path.write_text(f"54321:{boundary_timestamp}")

        # At the boundary (time.time() - ts == 7200), the condition > 7200 is False
        # so the lock should be considered active
        with patch("zerg.commands._utils.time") as mock_time:
            mock_time.time.return_value = current_time
            result = acquire_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is False

    # --- F1: Atomic race simulation ---

    def test_atomic_acquire_race_simulation(self, tmp_path: Path) -> None:
        """F1: When os.open raises FileExistsError (another process won the race),
        acquire returns False without corrupting state."""
        gsd_dir = str(tmp_path)
        feature = "race-feature"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)

        with patch("zerg.commands._utils.os.open", side_effect=FileExistsError):
            result = acquire_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is False

    # --- F3: Read error resilience ---

    def test_acquire_handles_read_error_on_existing_lock(self, tmp_path: Path) -> None:
        """F3: When read_text raises OSError on existing lock, acquire removes
        the unreadable lock and creates a new one."""
        gsd_dir = str(tmp_path)
        feature = "read-err-feature"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"
        lock_path.write_text("placeholder")

        original_read_text = Path.read_text

        def failing_read_text(self_path, *args, **kwargs):
            if self_path.name == ".lock":
                raise OSError("Permission denied")
            return original_read_text(self_path, *args, **kwargs)

        with patch.object(Path, "read_text", failing_read_text):
            result = acquire_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is True
        content = lock_path.read_text().strip()
        pid_str, _ = content.split(":", 1)
        assert int(pid_str) == os.getpid()

    # --- F4: Path traversal rejection ---

    def test_acquire_rejects_path_traversal(self, tmp_path: Path) -> None:
        """F4: Feature name with '..' raises ValueError."""
        with pytest.raises(ValueError, match="Invalid feature name"):
            acquire_feature_lock("../etc", gsd_dir=str(tmp_path))

    def test_acquire_rejects_slash_in_name(self, tmp_path: Path) -> None:
        """F4: Feature name with '/' raises ValueError."""
        with pytest.raises(ValueError, match="Invalid feature name"):
            acquire_feature_lock("foo/bar", gsd_dir=str(tmp_path))

    def test_acquire_rejects_backslash_in_name(self, tmp_path: Path) -> None:
        """F4: Feature name with backslash raises ValueError."""
        with pytest.raises(ValueError, match="Invalid feature name"):
            acquire_feature_lock("foo\\bar", gsd_dir=str(tmp_path))

    def test_acquire_rejects_empty_name(self, tmp_path: Path) -> None:
        """F4: Empty feature name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid feature name"):
            acquire_feature_lock("", gsd_dir=str(tmp_path))


class TestReleaseFeatureLock:
    """Tests for release_feature_lock()."""

    def test_removes_lock_file(self, tmp_path: Path) -> None:
        """Lock file is removed on release."""
        gsd_dir = str(tmp_path)
        feature = "release-me"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"
        lock_path.write_text(f"{os.getpid()}:{time.time()}")

        release_feature_lock(feature, gsd_dir=gsd_dir)

        assert not lock_path.exists()

    def test_no_error_when_lock_does_not_exist(self, tmp_path: Path) -> None:
        """No error raised when releasing a lock that does not exist."""
        gsd_dir = str(tmp_path)
        feature = "no-lock-here"

        # Should not raise
        release_feature_lock(feature, gsd_dir=gsd_dir)

    def test_no_error_when_spec_dir_does_not_exist(self, tmp_path: Path) -> None:
        """No error raised when the spec directory itself does not exist."""
        gsd_dir = str(tmp_path)
        feature = "nonexistent-spec"

        # The specs/feature directory does not exist at all
        assert not (tmp_path / "specs" / feature).exists()

        # Should not raise
        release_feature_lock(feature, gsd_dir=gsd_dir)

    # --- F2: Ownership-validated release ---

    def test_release_only_deletes_owned_lock(self, tmp_path: Path) -> None:
        """F2: Lock owned by a different PID is NOT deleted on release."""
        gsd_dir = str(tmp_path)
        feature = "other-pid"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        # Write lock with a PID that is not ours
        other_pid = os.getpid() + 1
        lock_path.write_text(f"{other_pid}:{time.time()}")

        release_feature_lock(feature, gsd_dir=gsd_dir)

        # Lock should still exist because it belongs to another process
        assert lock_path.exists()
        content = lock_path.read_text()
        assert content.startswith(f"{other_pid}:")

    def test_release_deletes_own_lock(self, tmp_path: Path) -> None:
        """F2: Lock owned by the current PID IS deleted on release."""
        gsd_dir = str(tmp_path)
        feature = "own-pid"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        lock_path.write_text(f"{os.getpid()}:{time.time()}")

        release_feature_lock(feature, gsd_dir=gsd_dir)

        assert not lock_path.exists()

    def test_release_deletes_corrupt_lock(self, tmp_path: Path) -> None:
        """F2: Corrupt (unparseable) lock is deleted as fallback cleanup."""
        gsd_dir = str(tmp_path)
        feature = "corrupt-release"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        lock_path.write_text("not-a-valid-lock")

        release_feature_lock(feature, gsd_dir=gsd_dir)

        # Corrupt locks are deleted as cleanup fallback
        assert not lock_path.exists()

    # --- F4: Path traversal rejection ---

    def test_release_rejects_path_traversal(self, tmp_path: Path) -> None:
        """F4: Feature name with '..' raises ValueError."""
        with pytest.raises(ValueError, match="Invalid feature name"):
            release_feature_lock("../etc", gsd_dir=str(tmp_path))


class TestCheckFeatureLock:
    """Tests for check_feature_lock()."""

    def test_returns_dict_for_active_lock(self, tmp_path: Path) -> None:
        """Returns dict with pid, timestamp, age_seconds for active lock."""
        gsd_dir = str(tmp_path)
        feature = "active-check"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        current_time = 1700000000.0
        lock_timestamp = current_time - 300  # 5 minutes ago
        lock_path.write_text(f"42:{lock_timestamp}")

        with patch("zerg.commands._utils.time") as mock_time:
            mock_time.time.return_value = current_time
            result = check_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is not None
        assert result["pid"] == 42
        assert result["timestamp"] == lock_timestamp
        assert result["age_seconds"] == pytest.approx(300.0, abs=1.0)

    def test_returns_none_when_no_lock(self, tmp_path: Path) -> None:
        """Returns None when no lock file exists."""
        gsd_dir = str(tmp_path)
        feature = "unlocked"

        result = check_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is None

    def test_returns_none_when_lock_is_stale(self, tmp_path: Path) -> None:
        """Returns None when the lock is older than 2 hours (stale)."""
        gsd_dir = str(tmp_path)
        feature = "stale-check"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        # Lock from 3 hours ago
        stale_timestamp = time.time() - 10800
        lock_path.write_text(f"12345:{stale_timestamp}")

        result = check_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is None

    def test_returns_none_for_corrupt_lock(self, tmp_path: Path) -> None:
        """Returns None for a lock file with corrupt/unparseable content."""
        gsd_dir = str(tmp_path)
        feature = "corrupt-check"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        lock_path.write_text("garbage-data-no-colon")

        result = check_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is None

    def test_returns_none_for_empty_lock_file(self, tmp_path: Path) -> None:
        """Returns None for an empty lock file."""
        gsd_dir = str(tmp_path)
        feature = "empty-lock"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        lock_path.write_text("")

        result = check_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is None

    def test_returns_none_for_non_numeric_pid(self, tmp_path: Path) -> None:
        """Returns None when the PID portion is not a valid integer."""
        gsd_dir = str(tmp_path)
        feature = "bad-pid"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        lock_path.write_text(f"not-a-pid:{time.time()}")

        result = check_feature_lock(feature, gsd_dir=gsd_dir)

        # check_feature_lock parses pid with int() which raises ValueError
        # for non-numeric strings, but the try/except catches ValueError
        # Note: the int() call happens AFTER the stale check, so the function
        # will attempt int("not-a-pid") which raises ValueError -> returns None
        assert result is None

    # --- F3: Read error resilience ---

    def test_check_handles_read_error(self, tmp_path: Path) -> None:
        """F3: When read_text raises OSError, check returns None gracefully."""
        gsd_dir = str(tmp_path)
        feature = "read-err-check"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"
        lock_path.write_text("placeholder")

        original_read_text = Path.read_text

        def failing_read_text(self_path, *args, **kwargs):
            if self_path.name == ".lock":
                raise PermissionError("Permission denied")
            return original_read_text(self_path, *args, **kwargs)

        with patch.object(Path, "read_text", failing_read_text):
            result = check_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is None

    # --- F4: Path traversal rejection ---

    def test_check_rejects_path_traversal(self, tmp_path: Path) -> None:
        """F4: Feature name with '..' raises ValueError."""
        with pytest.raises(ValueError, match="Invalid feature name"):
            check_feature_lock("../etc", gsd_dir=str(tmp_path))

    # --- F5: PID/timestamp bounds checking ---

    def test_pid_zero_treated_as_corrupt(self, tmp_path: Path) -> None:
        """F5: PID of 0 is out of bounds and treated as corrupt (returns None)."""
        gsd_dir = str(tmp_path)
        feature = "pid-zero"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        lock_path.write_text(f"0:{time.time()}")

        result = check_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is None

    def test_negative_pid_treated_as_corrupt(self, tmp_path: Path) -> None:
        """F5: Negative PID is out of bounds and treated as corrupt."""
        gsd_dir = str(tmp_path)
        feature = "pid-negative"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        lock_path.write_text(f"-1:{time.time()}")

        result = check_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is None

    def test_pid_over_max_treated_as_corrupt(self, tmp_path: Path) -> None:
        """F5: PID > 4194304 (MAX_PID) is out of bounds and treated as corrupt."""
        gsd_dir = str(tmp_path)
        feature = "pid-over-max"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        lock_path.write_text(f"4194305:{time.time()}")

        result = check_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is None

    def test_future_timestamp_treated_as_corrupt(self, tmp_path: Path) -> None:
        """F5: Timestamp far in the future (> now + 1 day) is treated as corrupt."""
        gsd_dir = str(tmp_path)
        feature = "ts-future"
        lock_dir = tmp_path / "specs" / feature
        lock_dir.mkdir(parents=True)
        lock_path = lock_dir / ".lock"

        # Timestamp 2 days in the future exceeds the +86400 bound
        future_ts = time.time() + 172800
        lock_path.write_text(f"1000:{future_ts}")

        result = check_feature_lock(feature, gsd_dir=gsd_dir)

        assert result is None
