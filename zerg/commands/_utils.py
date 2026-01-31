"""Shared utilities for ZERG CLI commands."""

from pathlib import Path

from zerg.constants import GSD_DIR, STATE_DIR


def detect_feature() -> str | None:
    """Detect active feature from project state.

    Priority order:
    1. .gsd/.current-feature (explicit user intent from /zerg:plan)
    2. .zerg/state/*.json (most recently modified state file)

    The .gsd/.current-feature file is written by /zerg:plan and reflects the
    feature the user is actively working on. State JSON files may be stale
    from previous runs, so they serve as a fallback.

    Returns:
        Feature name or None if no active feature can be detected.
    """
    # Primary: explicit feature set by /zerg:plan
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
