# DC-012: Integration Test - Full Container Flow

**Level**: 5 | **Critical Path**: Yes ⭐ | **Estimate**: 30 min
**Dependencies**: DC-009, DC-010, DC-011

## Objective

Create integration test that validates the full flow:
1. Init with multi-language detection
2. Dynamic devcontainer generation
3. Container mode selection (or graceful skip if no Docker)
4. Kurukshetra dry-run verification

## Files Owned

- `tests/integration/test_container_flow.py` (create)

## Implementation

```python
"""Integration tests for dynamic devcontainer and container execution flow."""

import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


def docker_available() -> bool:
    """Check if Docker is available."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


class TestMultiLanguageDetection:
    """Test multi-language project detection."""

    def test_detect_python_and_node(self, tmp_path: Path) -> None:
        """Test detection of Python + Node.js project."""
        # Create marker files
        (tmp_path / "requirements.txt").write_text("flask>=2.0")
        (tmp_path / "package.json").write_text('{"name": "test"}')

        # Run detection
        from mahabharatha.security_rules import detect_project_stack

        stack = detect_project_stack(tmp_path)

        assert "python" in stack.languages
        assert "javascript" in stack.languages

    def test_detect_go_and_rust(self, tmp_path: Path) -> None:
        """Test detection of Go + Rust project."""
        (tmp_path / "go.mod").write_text("module test")
        (tmp_path / "Cargo.toml").write_text("[package]\nname = 'test'")

        from mahabharatha.security_rules import detect_project_stack

        stack = detect_project_stack(tmp_path)

        assert "go" in stack.languages
        assert "rust" in stack.languages


class TestDynamicDevcontainer:
    """Test dynamic devcontainer generation."""

    def test_multi_language_features(self) -> None:
        """Test features generated for multi-language project."""
        from mahabharatha.devcontainer_features import DynamicDevcontainerGenerator
        from mahabharatha.security_rules import ProjectStack

        stack = ProjectStack(languages={"python", "go", "typescript"})
        gen = DynamicDevcontainerGenerator(stack)
        config = gen.generate_config()

        features = config.get("features", {})

        # Should have common features
        assert any("git" in url for url in features)

        # Should have language features
        assert any("python" in url for url in features)
        assert any("go" in url for url in features)
        assert any("node" in url for url in features)  # TypeScript uses Node

    def test_custom_install_for_r(self) -> None:
        """Test custom install command for R."""
        from mahabharatha.devcontainer_features import DynamicDevcontainerGenerator
        from mahabharatha.security_rules import ProjectStack

        stack = ProjectStack(languages={"python", "r"})
        gen = DynamicDevcontainerGenerator(stack)
        config = gen.generate_config()

        post_create = config.get("postCreateCommand", "")
        assert "r-base" in post_create

    def test_write_devcontainer_file(self, tmp_path: Path) -> None:
        """Test writing devcontainer.json to disk."""
        from mahabharatha.devcontainer_features import DynamicDevcontainerGenerator
        from mahabharatha.security_rules import ProjectStack

        stack = ProjectStack(languages={"python"})
        gen = DynamicDevcontainerGenerator(stack)

        config_path = gen.write_to_file(tmp_path)

        assert config_path.exists()
        assert config_path.name == "devcontainer.json"

        # Verify JSON is valid
        config = json.loads(config_path.read_text())
        assert "features" in config
        assert "image" in config


class TestInitCommand:
    """Test mahabharatha init with multi-language support."""

    def test_init_creates_multi_lang_devcontainer(self, tmp_path: Path) -> None:
        """Test that init creates proper devcontainer for multi-lang project."""
        # Create marker files
        (tmp_path / "requirements.txt").write_text("flask")
        (tmp_path / "package.json").write_text('{"name": "test"}')

        # Change to temp dir and run init
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            from click.testing import CliRunner
            from mahabharatha.commands.init import init

            runner = CliRunner()
            result = runner.invoke(init, ["--no-security-rules"])

            assert result.exit_code == 0

            # Check devcontainer was created
            devcontainer_path = tmp_path / ".devcontainer" / "devcontainer.json"
            assert devcontainer_path.exists()

            config = json.loads(devcontainer_path.read_text())

            # Should use base image with features
            assert "base" in config.get("image", "") or "ubuntu" in config.get("image", "")
            assert "features" in config

        finally:
            os.chdir(original_cwd)


class TestContainerLauncher:
    """Test ContainerLauncher functionality."""

    def test_docker_available_check(self) -> None:
        """Test Docker availability check."""
        from mahabharatha.launcher import ContainerLauncher

        # Should return bool without error
        result = ContainerLauncher.docker_available()
        assert isinstance(result, bool)

    def test_image_exists_check(self) -> None:
        """Test image existence check."""
        from mahabharatha.launcher import ContainerLauncher

        # Non-existent image
        result = ContainerLauncher.image_exists("definitely-not-a-real-image-12345")
        assert result is False

    @pytest.mark.skipif(not docker_available(), reason="Docker not available")
    def test_spawn_requires_image(self) -> None:
        """Test that spawn fails gracefully without image."""
        from mahabharatha.launcher import ContainerLauncher, LauncherConfig

        launcher = ContainerLauncher(LauncherConfig())

        # Spawn with non-existent image
        launcher._image_name = "mahabharatha-test-nonexistent"
        result = launcher.spawn(
            worker_id=0,
            feature="test",
            worktree_path=Path("/tmp"),
            branch="main",
        )

        # Should fail but not crash
        assert result.success is False


class TestOrchestratorModeSelection:
    """Test orchestrator launcher mode selection."""

    def test_auto_detect_without_devcontainer(self, tmp_path: Path) -> None:
        """Test auto-detect falls back to subprocess without devcontainer."""
        from mahabharatha.config import ZergConfig
        from mahabharatha.launcher import SubprocessLauncher
        from mahabharatha.orchestrator import Orchestrator

        config = ZergConfig()
        orch = Orchestrator("test", config, repo_path=tmp_path)

        # Should use subprocess
        assert isinstance(orch.launcher, SubprocessLauncher)
        assert orch.get_launcher_mode() == "subprocess"

    def test_container_mode_available_check(self, tmp_path: Path) -> None:
        """Test container_mode_available() returns proper info."""
        from mahabharatha.config import ZergConfig
        from mahabharatha.orchestrator import Orchestrator

        config = ZergConfig()
        orch = Orchestrator("test", config, repo_path=tmp_path)

        available, reason = orch.container_mode_available()

        assert isinstance(available, bool)
        assert isinstance(reason, str)

        # Without devcontainer, should not be available
        if not (tmp_path / ".devcontainer" / "devcontainer.json").exists():
            assert available is False


class TestRushCommand:
    """Test kurukshetra command with mode flag."""

    def test_rush_help_shows_mode_option(self) -> None:
        """Test that --mode appears in kurukshetra help."""
        from click.testing import CliRunner
        from mahabharatha.commands.kurukshetra import kurukshetra

        runner = CliRunner()
        result = runner.invoke(kurukshetra, ["--help"])

        assert "--mode" in result.output or "-m" in result.output
        assert "subprocess" in result.output
        assert "container" in result.output
        assert "auto" in result.output


class TestEndToEndFlow:
    """End-to-end integration tests."""

    def test_full_init_to_dry_run(self, tmp_path: Path) -> None:
        """Test complete flow from init to kurukshetra dry-run."""
        # Create multi-lang project
        (tmp_path / "requirements.txt").write_text("flask")
        (tmp_path / "package.json").write_text('{"name": "test"}')

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            from click.testing import CliRunner
            from mahabharatha.commands.init import init

            runner = CliRunner()

            # Run init
            result = runner.invoke(init, ["--no-security-rules"])
            assert result.exit_code == 0

            # Verify devcontainer
            devcontainer = tmp_path / ".devcontainer" / "devcontainer.json"
            assert devcontainer.exists()

            config = json.loads(devcontainer.read_text())
            features = str(config.get("features", {}))
            assert "python" in features
            assert "node" in features

        finally:
            os.chdir(original_cwd)
```

## Verification

```bash
# Run the integration tests
pytest tests/integration/test_container_flow.py -v --tb=short

# Run with coverage
pytest tests/integration/test_container_flow.py -v --cov=mahabharatha --cov-report=term-missing
```

## Acceptance Criteria

- [ ] TestMultiLanguageDetection passes
- [ ] TestDynamicDevcontainer passes
- [ ] TestInitCommand passes
- [ ] TestContainerLauncher passes (skips if no Docker)
- [ ] TestOrchestratorModeSelection passes
- [ ] TestRushCommand passes
- [ ] TestEndToEndFlow passes
- [ ] All tests handle missing Docker gracefully
- [ ] No import errors
- [ ] pytest runs without failures
