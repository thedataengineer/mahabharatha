"""Git hook management for ZERG.

Migrated from zerg/security.py — contains hook install/uninstall functions.
"""

import shutil
import stat
from pathlib import Path

from zerg.logging import get_logger

logger = get_logger("security")


def install_hooks(repo_path: str | Path = ".") -> bool:
    """Install ZERG git hooks to the repository.

    Args:
        repo_path: Path to repository

    Returns:
        True if hooks were installed successfully
    """
    repo = Path(repo_path).resolve()
    git_hooks_dir = repo / ".git" / "hooks"
    zerg_hooks_dir = repo / ".zerg" / "hooks"

    if not git_hooks_dir.exists():
        logger.error(f"Git hooks directory not found: {git_hooks_dir}")
        return False

    if not zerg_hooks_dir.exists():
        logger.warning(f"ZERG hooks directory not found: {zerg_hooks_dir}")
        return False

    installed = 0

    for hook_file in zerg_hooks_dir.iterdir():
        if hook_file.is_file() and not hook_file.name.startswith("."):
            target = git_hooks_dir / hook_file.name

            # Backup existing hook if present
            if target.exists():
                backup = target.with_suffix(".backup")
                shutil.copy2(target, backup)
                logger.info(f"Backed up existing {hook_file.name} to {backup.name}")

            # Copy hook
            shutil.copy2(hook_file, target)

            # Make executable
            target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            logger.info(f"Installed hook: {hook_file.name}")
            installed += 1

    logger.info(f"Installed {installed} hooks to {git_hooks_dir}")
    return installed > 0


def uninstall_hooks(repo_path: str | Path = ".") -> bool:
    """Uninstall ZERG git hooks from the repository.

    Args:
        repo_path: Path to repository

    Returns:
        True if hooks were uninstalled successfully
    """
    repo = Path(repo_path).resolve()
    git_hooks_dir = repo / ".git" / "hooks"
    zerg_hooks_dir = repo / ".zerg" / "hooks"

    if not git_hooks_dir.exists():
        logger.error(f"Git hooks directory not found: {git_hooks_dir}")
        return False

    uninstalled = 0

    for hook_file in zerg_hooks_dir.iterdir():
        if hook_file.is_file() and not hook_file.name.startswith("."):
            target = git_hooks_dir / hook_file.name

            if target.exists():
                target.unlink()
                logger.info(f"Removed hook: {hook_file.name}")
                uninstalled += 1

                # Restore backup if exists
                backup = target.with_suffix(".backup")
                if backup.exists():
                    shutil.move(backup, target)
                    logger.info(f"Restored backup for {hook_file.name}")

    logger.info(f"Uninstalled {uninstalled} hooks from {git_hooks_dir}")
    return uninstalled > 0
