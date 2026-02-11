"""Shared utilities for ZERG CLI commands."""

import os
import time
from pathlib import Path

from zerg.constants import GSD_DIR, STATE_DIR


def detect_feature() -> str | None:
    """Detect active feature from project state.

    Priority order:
    1. ZERG_FEATURE env var (terminal-session-scoped, multi-epic safe)
    2. .gsd/.current-feature (explicit user intent from /zerg:plan)
    3. .zerg/state/*.json (most recently modified state file)

    The ZERG_FEATURE env var allows terminal-scoped feature isolation,
    enabling multiple epics to run concurrently in separate terminals.

    The .gsd/.current-feature file is written by /zerg:plan and reflects the
    feature the user is actively working on. State JSON files may be stale
    from previous runs, so they serve as a fallback.

    Returns:
        Feature name or None if no active feature can be detected.
    """
    # Primary: env var (terminal-scoped, multi-epic safe)
    env_feature = os.environ.get("ZERG_FEATURE", "").strip()
    if env_feature:
        return env_feature

    # Secondary: explicit feature set by /zerg:plan
    current_feature = Path(GSD_DIR) / ".current-feature"
    if current_feature.exists():
        name = current_feature.read_text().strip()
        if name:
            return name

    # Fallback: most recently modified state file
    state_dir = Path(STATE_DIR)
    if state_dir.exists():
        state_files = list(state_dir.glob("*.json"))
        if state_files:
            state_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return state_files[0].stem

    return None


def acquire_feature_lock(feature: str, gsd_dir: str = ".gsd") -> bool:
    """Create advisory lock for a feature.

    Returns True if lock acquired, False if another session holds it.
    Locks older than 2 hours are considered stale and automatically removed.

    Args:
        feature: Feature name to lock.
        gsd_dir: Path to the GSD directory.

    Returns:
        True if the lock was acquired, False if an active lock exists.
    """
    lock_path = Path(gsd_dir) / "specs" / feature / ".lock"
    if lock_path.exists():
        content = lock_path.read_text().strip()
        try:
            pid_str, ts_str = content.split(":", 1)
            ts = float(ts_str)
            if time.time() - ts > 7200:  # Stale if > 2 hours
                lock_path.unlink()
            else:
                return False  # Active lock
        except (ValueError, OSError):
            lock_path.unlink()  # Corrupt lock, remove
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(f"{os.getpid()}:{time.time()}")
    return True


def release_feature_lock(feature: str, gsd_dir: str = ".gsd") -> None:
    """Release advisory lock for a feature.

    Args:
        feature: Feature name to unlock.
        gsd_dir: Path to the GSD directory.
    """
    lock_path = Path(gsd_dir) / "specs" / feature / ".lock"
    if lock_path.exists():
        lock_path.unlink(missing_ok=True)


def check_feature_lock(feature: str, gsd_dir: str = ".gsd") -> dict | None:
    """Check if a feature is locked.

    Returns lock info dict if an active lock exists, or None if unlocked
    or the lock is stale (older than 2 hours).

    Args:
        feature: Feature name to check.
        gsd_dir: Path to the GSD directory.

    Returns:
        Dict with pid, timestamp, and age_seconds if locked; None otherwise.
    """
    lock_path = Path(gsd_dir) / "specs" / feature / ".lock"
    if not lock_path.exists():
        return None
    content = lock_path.read_text().strip()
    try:
        pid_str, ts_str = content.split(":", 1)
        ts = float(ts_str)
        if time.time() - ts > 7200:
            return None  # Stale
        return {"pid": int(pid_str), "timestamp": ts, "age_seconds": time.time() - ts}
    except (ValueError, OSError):
        return None
