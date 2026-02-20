"""Tests for MAHABHARATHA v2 Container Launcher."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

# Check if Docker is available
try:
    import docker

    docker.from_env().ping()
    DOCKER_AVAILABLE = True
except Exception:
    DOCKER_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not DOCKER_AVAILABLE, reason="Docker not available"
)


class TestContainerConfig:
    """Tests for ContainerConfig dataclass."""

    def test_container_config_creation(self, tmp_path):
        """Test ContainerConfig can be created."""
        from container import ContainerConfig

        config = ContainerConfig(
            image="python:3.11-slim",
            worktree_path=tmp_path,
            env_vars={"TEST": "1"},
            ports=[8080],
        )
        assert config.image == "python:3.11-slim"
        assert config.worktree_path == tmp_path
        assert config.env_vars == {"TEST": "1"}
        assert config.ports == [8080]

    def test_container_config_defaults(self, tmp_path):
        """Test ContainerConfig default values."""
        from container import ContainerConfig

        config = ContainerConfig(
            image="python:3.11-slim",
            worktree_path=tmp_path,
            env_vars={},
            ports=[],
        )
        assert config.memory_limit == "4g"
        assert config.cpu_limit == 2.0
        assert config.network == "mahabharatha-internal"


class TestRunningContainer:
    """Tests for RunningContainer dataclass."""

    def test_running_container_creation(self, tmp_path):
        """Test RunningContainer can be created."""
        from datetime import datetime

        from container import RunningContainer

        rc = RunningContainer(
            container_id="abc123",
            worker_id="W1",
            worktree_path=tmp_path,
            ports=[8080],
            started_at=datetime.now(),
        )
        assert rc.container_id == "abc123"
        assert rc.worker_id == "W1"


class TestResourceLimits:
    """Tests for ResourceLimits dataclass."""

    def test_resource_limits_defaults(self):
        """Test ResourceLimits default values."""
        from container import ResourceLimits

        rl = ResourceLimits()
        assert rl.memory == "4g"
        assert rl.cpus == 2.0

    def test_resource_limits_from_config(self):
        """Test ResourceLimits.from_config factory."""
        from container import ResourceLimits

        config = {"memory_limit": "2g", "cpu_limit": 1.0}
        rl = ResourceLimits.from_config(config)
        assert rl.memory == "2g"
        assert rl.cpus == 1.0

    def test_resource_limits_from_config_defaults(self):
        """Test ResourceLimits.from_config with empty config."""
        from container import ResourceLimits

        rl = ResourceLimits.from_config({})
        assert rl.memory == "4g"
        assert rl.cpus == 2.0


class TestContainerLauncherInit:
    """Tests for ContainerLauncher initialization."""

    def test_launcher_initialization(self):
        """Test ContainerLauncher initializes correctly."""
        from container import ContainerLauncher

        cl = ContainerLauncher()
        assert cl.containers == {}
        assert cl.client is not None

    def test_launcher_ensures_network(self):
        """Test ContainerLauncher creates network if needed."""
        import docker
        from container import ContainerLauncher

        ContainerLauncher()  # Initialize to create network
        # Network should exist after initialization
        client = docker.from_env()
        networks = [n.name for n in client.networks.list()]
        assert "mahabharatha-internal" in networks


class TestContainerLauncherOperations:
    """Tests for ContainerLauncher container operations."""

    @pytest.fixture
    def launcher(self):
        """Provide a ContainerLauncher instance."""
        from container import ContainerLauncher

        return ContainerLauncher()

    @pytest.fixture
    def config(self, tmp_path):
        """Provide a basic ContainerConfig."""
        from container import ContainerConfig

        return ContainerConfig(
            image="python:3.11-slim",
            worktree_path=tmp_path,
            env_vars={"TEST_VAR": "hello"},
            ports=[],
        )

    def test_launch_container(self, launcher, config):
        """Test launching a container."""
        running = launcher.launch("w1", config)
        try:
            assert running.worker_id == "w1"
            assert running.container_id is not None
            assert launcher.is_running("w1")
        finally:
            launcher.stop("w1")

    def test_stop_container(self, launcher, config):
        """Test stopping a container."""
        launcher.launch("w1", config)
        launcher.stop("w1")
        assert not launcher.is_running("w1")
        assert "w1" not in launcher.containers

    def test_stop_nonexistent_container(self, launcher):
        """Test stopping nonexistent container doesn't raise."""
        launcher.stop("nonexistent")  # Should not raise

    def test_is_running_false_for_nonexistent(self, launcher):
        """Test is_running returns False for nonexistent worker."""
        assert not launcher.is_running("nonexistent")

    def test_get_logs(self, launcher, config):
        """Test getting container logs."""
        launcher.launch("w1", config)
        try:
            logs = launcher.get_logs("w1")
            assert isinstance(logs, str)
        finally:
            launcher.stop("w1")

    def test_get_logs_nonexistent(self, launcher):
        """Test get_logs returns empty for nonexistent worker."""
        logs = launcher.get_logs("nonexistent")
        assert logs == ""

    def test_resource_limits_applied(self, launcher, config):
        """Test resource limits are applied to container."""
        import docker

        config.memory_limit = "2g"
        config.cpu_limit = 1.0
        running = launcher.launch("w1", config)
        try:
            client = docker.from_env()
            container = client.containers.get(running.container_id)
            # Check memory limit (in bytes)
            assert container.attrs["HostConfig"]["Memory"] == 2 * 1024**3
            # Check CPU limit (in nano-cpus)
            assert container.attrs["HostConfig"]["NanoCpus"] == int(1.0 * 1e9)
        finally:
            launcher.stop("w1")

    def test_environment_variables_injected(self, launcher, config):
        """Test environment variables are injected."""
        import docker

        running = launcher.launch("w1", config)
        try:
            client = docker.from_env()
            container = client.containers.get(running.container_id)
            env = container.attrs["Config"]["Env"]
            assert any("ZERG_WORKER_ID=w1" in e for e in env)
            assert any("TEST_VAR=hello" in e for e in env)
        finally:
            launcher.stop("w1")

    def test_worktree_mounted(self, launcher, config, tmp_path):
        """Test worktree is mounted as volume."""
        import docker

        running = launcher.launch("w1", config)
        try:
            client = docker.from_env()
            container = client.containers.get(running.container_id)
            mounts = container.attrs["Mounts"]
            workspace_mount = next(
                (m for m in mounts if m["Destination"] == "/workspace"), None
            )
            assert workspace_mount is not None
            assert str(tmp_path.absolute()) in workspace_mount["Source"]
        finally:
            launcher.stop("w1")


class TestContainerCleanup:
    """Tests for container cleanup on failures."""

    @pytest.fixture
    def launcher(self):
        """Provide a ContainerLauncher instance."""
        from container import ContainerLauncher

        return ContainerLauncher()

    def test_container_removed_after_stop(self, launcher, tmp_path):
        """Test container is removed after stop."""
        import docker
        from container import ContainerConfig

        config = ContainerConfig(
            image="python:3.11-slim",
            worktree_path=tmp_path,
            env_vars={},
            ports=[],
        )
        running = launcher.launch("w1", config)
        container_id = running.container_id

        launcher.stop("w1")

        # Container should be removed
        client = docker.from_env()
        with pytest.raises(docker.errors.NotFound):
            client.containers.get(container_id)
