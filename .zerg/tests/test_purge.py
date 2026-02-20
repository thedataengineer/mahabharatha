"""Tests for MAHABHARATHA v2 Purge Command."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPurgeTarget:
    """Tests for PurgeTarget enum."""

    def test_targets_exist(self):
        """Test purge targets are defined."""
        from purge import PurgeTarget

        assert hasattr(PurgeTarget, "WORKTREES")
        assert hasattr(PurgeTarget, "LOGS")
        assert hasattr(PurgeTarget, "CHECKPOINTS")
        assert hasattr(PurgeTarget, "METRICS")
        assert hasattr(PurgeTarget, "SESSIONS")
        assert hasattr(PurgeTarget, "ALL")


class TestPurgeConfig:
    """Tests for PurgeConfig dataclass."""

    def test_config_defaults(self):
        """Test PurgeConfig default values."""
        from purge import PurgeConfig

        config = PurgeConfig()
        assert config.dry_run is False
        assert config.force is False
        assert config.preserve_specs is True

    def test_config_custom(self):
        """Test PurgeConfig with custom values."""
        from purge import PurgeConfig

        config = PurgeConfig(dry_run=True, force=True)
        assert config.dry_run is True
        assert config.force is True


class TestPurgeItem:
    """Tests for PurgeItem dataclass."""

    def test_item_creation(self):
        """Test PurgeItem can be created."""
        from purge import PurgeItem

        item = PurgeItem(path="/tmp/test", target_type="logs", size_bytes=1024)
        assert item.path == "/tmp/test"
        assert item.target_type == "logs"
        assert item.size_bytes == 1024

    def test_item_to_dict(self):
        """Test PurgeItem serialization."""
        from purge import PurgeItem

        item = PurgeItem(path="/tmp/file", target_type="checkpoints", size_bytes=512)
        data = item.to_dict()
        assert data["path"] == "/tmp/file"
        assert data["size_bytes"] == 512


class TestPurgeResult:
    """Tests for PurgeResult dataclass."""

    def test_result_success(self):
        """Test successful PurgeResult."""
        from purge import PurgeResult

        result = PurgeResult(success=True, items_removed=5, bytes_freed=10240)
        assert result.success is True
        assert result.items_removed == 5

    def test_result_with_errors(self):
        """Test PurgeResult with errors."""
        from purge import PurgeResult

        result = PurgeResult(
            success=False,
            items_removed=3,
            bytes_freed=5000,
            errors=["Failed to remove /tmp/locked"],
        )
        assert result.success is False
        assert len(result.errors) == 1

    def test_result_to_dict(self):
        """Test PurgeResult serialization."""
        from purge import PurgeResult

        result = PurgeResult(success=True, items_removed=10, bytes_freed=50000)
        data = result.to_dict()
        assert data["success"] is True
        assert data["bytes_freed"] == 50000


class TestPurgeManager:
    """Tests for PurgeManager."""

    def test_manager_creation(self):
        """Test PurgeManager can be created."""
        from purge import PurgeManager

        manager = PurgeManager()
        assert manager is not None

    def test_manager_has_target_paths(self):
        """Test PurgeManager defines target paths."""
        from purge import PurgeManager, PurgeTarget

        assert PurgeTarget.WORKTREES in PurgeManager.TARGET_PATHS
        assert PurgeTarget.LOGS in PurgeManager.TARGET_PATHS

    def test_scan_empty(self):
        """Test scanning non-existent paths."""
        from purge import PurgeManager, PurgeTarget

        manager = PurgeManager(base_path="/nonexistent")
        items = manager.scan([PurgeTarget.LOGS])
        assert items == []


class TestPurgeCommand:
    """Tests for PurgeCommand."""

    def test_command_creation(self):
        """Test PurgeCommand can be created."""
        from purge import PurgeCommand

        cmd = PurgeCommand()
        assert cmd is not None

    def test_command_dry_run(self):
        """Test dry run mode."""
        from purge import PurgeCommand, PurgeResult

        cmd = PurgeCommand()
        result = cmd.run(targets=["logs"], dry_run=True)
        assert isinstance(result, PurgeResult)

    def test_command_format_text(self):
        """Test text output formatting."""
        from purge import PurgeCommand, PurgeResult

        cmd = PurgeCommand()
        result = PurgeResult(success=True, items_removed=3, bytes_freed=4096)
        output = cmd.format_result(result, format="text")
        assert "Purge Result" in output
        assert "Items Removed: 3" in output

    def test_command_format_json(self):
        """Test JSON output formatting."""
        import json

        from purge import PurgeCommand, PurgeResult

        cmd = PurgeCommand()
        result = PurgeResult(success=True, items_removed=1, bytes_freed=100)
        output = cmd.format_result(result, format="json")
        data = json.loads(output)
        assert data["success"] is True
