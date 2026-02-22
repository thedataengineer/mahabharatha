"""MAHABHARATHA v2 Purge Command - Artifact and worktree cleanup."""

import contextlib
import json
import shutil
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class PurgeTarget(Enum):
    """Purge targets."""

    WORKTREES = "worktrees"
    LOGS = "logs"
    CHECKPOINTS = "checkpoints"
    METRICS = "metrics"
    SESSIONS = "sessions"
    ALL = "all"


@dataclass
class PurgeConfig:
    """Configuration for purge operations."""

    dry_run: bool = False
    force: bool = False
    preserve_specs: bool = True


@dataclass
class PurgeItem:
    """An item to be purged."""

    path: str
    target_type: str
    size_bytes: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "target_type": self.target_type,
            "size_bytes": self.size_bytes,
        }


@dataclass
class PurgeResult:
    """Result of purge operation."""

    success: bool
    items_removed: int
    bytes_freed: int
    items: list[PurgeItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "items_removed": self.items_removed,
            "bytes_freed": self.bytes_freed,
            "items": [i.to_dict() for i in self.items],
            "errors": self.errors,
        }


class PurgeManager:
    """Manage artifact cleanup."""

    TARGET_PATHS = {
        PurgeTarget.WORKTREES: ".mahabharatha/worktrees",
        PurgeTarget.LOGS: ".mahabharatha/logs",
        PurgeTarget.CHECKPOINTS: ".mahabharatha/checkpoints",
        PurgeTarget.METRICS: ".mahabharatha/metrics",
        PurgeTarget.SESSIONS: ".mahabharatha/sessions",
    }

    def __init__(self, base_path: str = "."):
        """Initialize purge manager."""
        self.base_path = Path(base_path)

    def scan(self, targets: list[PurgeTarget]) -> list[PurgeItem]:
        """Scan for items to purge."""
        items = []

        for target in targets:
            if target == PurgeTarget.ALL:
                # Scan all targets
                for t, path in self.TARGET_PATHS.items():
                    items.extend(self._scan_path(path, t.value))
            else:
                path = self.TARGET_PATHS.get(target, "")
                if path:
                    items.extend(self._scan_path(path, target.value))

        return items

    def _scan_path(self, rel_path: str, target_type: str) -> list[PurgeItem]:
        """Scan a path for items."""
        items = []
        full_path = self.base_path / rel_path

        if full_path.exists():
            for item in full_path.iterdir():
                size = self._get_size(item)
                items.append(
                    PurgeItem(
                        path=str(item),
                        target_type=target_type,
                        size_bytes=size,
                    )
                )

        return items

    def _get_size(self, path: Path) -> int:
        """Get size of file or directory."""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            total = 0
            for f in path.rglob("*"):
                if f.is_file():
                    total += f.stat().st_size
            return total
        return 0

    def purge(self, items: list[PurgeItem], dry_run: bool = False) -> PurgeResult:
        """Purge the specified items."""
        removed = 0
        freed = 0
        errors = []

        for item in items:
            if dry_run:
                removed += 1
                freed += item.size_bytes
                continue

            try:
                path = Path(item.path)
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    removed += 1
                    freed += item.size_bytes
            except OSError as e:
                errors.append(f"Failed to remove {item.path}: {e}")

        return PurgeResult(
            success=len(errors) == 0,
            items_removed=removed,
            bytes_freed=freed,
            items=items,
            errors=errors,
        )


class PurgeCommand:
    """Main purge command orchestrator."""

    def __init__(self, config: PurgeConfig | None = None):
        """Initialize purge command."""
        self.config = config or PurgeConfig()
        self.manager = PurgeManager()

    def run(
        self,
        targets: list[str],
        dry_run: bool = False,
    ) -> PurgeResult:
        """Run purge operation."""
        # Convert string targets to enum
        target_enums = []
        for t in targets:
            with contextlib.suppress(ValueError):
                target_enums.append(PurgeTarget(t))

        if not target_enums:
            target_enums = [PurgeTarget.ALL]

        # Scan for items
        items = self.manager.scan(target_enums)

        # Purge
        return self.manager.purge(items, dry_run=dry_run or self.config.dry_run)

    def format_result(self, result: PurgeResult, format: str = "text") -> str:
        """Format purge result."""
        if format == "json":
            return json.dumps(result.to_dict(), indent=2)

        # Format bytes
        if result.bytes_freed >= 1024 * 1024:
            size_str = f"{result.bytes_freed / (1024 * 1024):.1f} MB"
        elif result.bytes_freed >= 1024:
            size_str = f"{result.bytes_freed / 1024:.1f} KB"
        else:
            size_str = f"{result.bytes_freed} bytes"

        status = "✓" if result.success else "✗"
        lines = [
            "Purge Result",
            "=" * 40,
            f"Status: {status}",
            f"Items Removed: {result.items_removed}",
            f"Space Freed: {size_str}",
        ]

        if result.items:
            lines.append("")
            lines.append("Removed:")
            for item in result.items[:10]:
                lines.append(f"  - {item.path}")

        if result.errors:
            lines.append("")
            lines.append("Errors:")
            for error in result.errors:
                lines.append(f"  - {error}")

        return "\n".join(lines)


__all__ = [
    "PurgeTarget",
    "PurgeConfig",
    "PurgeItem",
    "PurgeResult",
    "PurgeManager",
    "PurgeCommand",
]
