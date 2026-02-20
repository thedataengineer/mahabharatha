"""MAHABHARATHA v2 Session Command - Session save/load for multi-session continuity."""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class SessionAction(Enum):
    """Session actions."""

    SAVE = "save"
    LOAD = "load"
    LIST = "list"
    DELETE = "delete"


@dataclass
class SessionConfig:
    """Configuration for session operations."""

    compress: bool = False
    session_dir: str = ".mahabharatha/sessions"


@dataclass
class SessionManifest:
    """Session manifest with metadata."""

    name: str
    created_at: str
    feature: str = ""
    level: int = 0
    tasks_complete: int = 0
    tasks_total: int = 0
    checksums: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "created_at": self.created_at,
            "feature": self.feature,
            "level": self.level,
            "tasks_complete": self.tasks_complete,
            "tasks_total": self.tasks_total,
            "checksums": self.checksums,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionManifest":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SessionResult:
    """Result of session operation."""

    success: bool
    action: str
    message: str
    session_name: str = ""
    sessions: list[SessionManifest] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "action": self.action,
            "message": self.message,
            "session_name": self.session_name,
            "sessions": [s.to_dict() for s in self.sessions],
        }


class SessionManager:
    """Manage session persistence."""

    def __init__(self, session_dir: str = ".mahabharatha/sessions"):
        """Initialize session manager."""
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, state_files: list[str]) -> SessionResult:
        """Save current session."""
        session_path = self.session_dir / name
        session_path.mkdir(parents=True, exist_ok=True)

        # Create manifest
        manifest = SessionManifest(
            name=name,
            created_at=datetime.now().isoformat(),
        )

        # Copy state files
        for filepath in state_files:
            src = Path(filepath)
            if src.exists():
                dst = session_path / src.name
                shutil.copy2(src, dst)

        # Save manifest
        manifest_path = session_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest.to_dict(), f, indent=2)

        return SessionResult(
            success=True,
            action="save",
            message=f"Session {name} saved",
            session_name=name,
        )

    def load(self, name: str) -> SessionResult:
        """Load a saved session."""
        session_path = self.session_dir / name
        if not session_path.exists():
            return SessionResult(
                success=False,
                action="load",
                message=f"Session {name} not found",
            )

        manifest_path = session_path / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                json.load(f)  # Validate manifest is readable

        return SessionResult(
            success=True,
            action="load",
            message=f"Session {name} loaded",
            session_name=name,
        )

    def list_sessions(self) -> SessionResult:
        """List all saved sessions."""
        sessions = []
        for session_path in self.session_dir.iterdir():
            if session_path.is_dir():
                manifest_path = session_path / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path) as f:
                        data = json.load(f)
                    sessions.append(SessionManifest.from_dict(data))

        return SessionResult(
            success=True,
            action="list",
            message=f"Found {len(sessions)} sessions",
            sessions=sessions,
        )

    def delete(self, name: str) -> SessionResult:
        """Delete a saved session."""
        session_path = self.session_dir / name
        if not session_path.exists():
            return SessionResult(
                success=False,
                action="delete",
                message=f"Session {name} not found",
            )

        shutil.rmtree(session_path)
        return SessionResult(
            success=True,
            action="delete",
            message=f"Session {name} deleted",
            session_name=name,
        )


class SessionCommand:
    """Main session command orchestrator."""

    def __init__(self, config: SessionConfig | None = None):
        """Initialize session command."""
        self.config = config or SessionConfig()
        self.manager = SessionManager(self.config.session_dir)

    def run(
        self, action: str, name: str = "", state_files: list[str] | None = None
    ) -> SessionResult:
        """Run session action."""
        if action == "save":
            return self.manager.save(name, state_files or [])
        elif action == "load":
            return self.manager.load(name)
        elif action == "list":
            return self.manager.list_sessions()
        elif action == "delete":
            return self.manager.delete(name)
        else:
            return SessionResult(
                success=False,
                action="unknown",
                message=f"Unknown action: {action}",
            )

    def format_result(self, result: SessionResult, format: str = "text") -> str:
        """Format session result."""
        if format == "json":
            return json.dumps(result.to_dict(), indent=2)

        lines = [
            "Session Operation",
            "=" * 40,
            f"Action: {result.action}",
            f"Status: {'✓' if result.success else '✗'}",
            f"Message: {result.message}",
        ]

        if result.sessions:
            lines.append("")
            lines.append("Sessions:")
            for s in result.sessions:
                lines.append(f"  - {s.name} ({s.created_at})")

        return "\n".join(lines)


__all__ = [
    "SessionAction",
    "SessionConfig",
    "SessionManifest",
    "SessionResult",
    "SessionManager",
    "SessionCommand",
]
