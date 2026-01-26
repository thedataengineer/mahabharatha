"""Tests for ZERG v2 Session Command."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSessionAction:
    """Tests for session actions."""

    def test_actions_exist(self):
        """Test session actions are defined."""
        from session import SessionAction

        assert hasattr(SessionAction, "SAVE")
        assert hasattr(SessionAction, "LOAD")
        assert hasattr(SessionAction, "LIST")
        assert hasattr(SessionAction, "DELETE")


class TestSessionManifest:
    """Tests for session manifest."""

    def test_manifest_creation(self):
        """Test SessionManifest can be created."""
        from session import SessionManifest

        manifest = SessionManifest(name="test", created_at="2026-01-25")
        assert manifest.name == "test"

    def test_manifest_to_dict(self):
        """Test SessionManifest serialization."""
        from session import SessionManifest

        manifest = SessionManifest(name="test", created_at="2026-01-25", level=2)
        data = manifest.to_dict()
        assert data["name"] == "test"
        assert data["level"] == 2


class TestSessionCommand:
    """Tests for SessionCommand."""

    def test_command_creation(self):
        """Test SessionCommand can be created."""
        from session import SessionCommand

        cmd = SessionCommand()
        assert cmd is not None

    def test_command_list(self):
        """Test listing sessions."""
        from session import SessionCommand, SessionResult

        cmd = SessionCommand()
        result = cmd.run(action="list")
        assert isinstance(result, SessionResult)
