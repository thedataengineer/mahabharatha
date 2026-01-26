"""Tests for ZERG containers module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from zerg.config import ZergConfig
from zerg.constants import WorkerStatus
from zerg.containers import ContainerInfo, ContainerManager
from zerg.exceptions import ContainerError


@pytest.fixture(autouse=True)
def mock_zerg_config():
    """Mock ZergConfig.load() for all container tests."""
    mock_config = MagicMock(spec=ZergConfig)
    mock_config.workers = MagicMock()
    mock_config.workers.max_workers = 5
    with patch.object(ZergConfig, "load", return_value=mock_config):
        yield mock_config


class TestContainerInfo:
    """Tests for ContainerInfo dataclass."""

    def test_creation(self) -> None:
        """Test creating container info."""
        info = ContainerInfo(
            container_id="abc123",
            name="zerg-worker-0",
            status="running",
            worker_id=0,
            port=49152,
            image="zerg-worker:latest",
        )

        assert info.container_id == "abc123"
        assert info.name == "zerg-worker-0"
        assert info.status == "running"
        assert info.worker_id == 0
        assert info.port == 49152
        assert info.image == "zerg-worker:latest"


class TestContainerManager:
    """Tests for ContainerManager class."""

    @pytest.fixture
    def mock_docker(self):
        """Mock Docker commands."""
        with patch.object(ContainerManager, "_run_docker") as mock:
            mock.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )
            yield mock

    @pytest.fixture
    def mock_compose(self):
        """Mock Docker Compose commands."""
        with patch.object(ContainerManager, "_run_compose") as mock:
            mock.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )
            yield mock

    def test_init_default(self, mock_docker) -> None:
        """Test default initialization."""
        with patch.object(ContainerManager, "_check_docker"):
            manager = ContainerManager()

        assert manager.compose_file == Path(".devcontainer/docker-compose.yaml")

    def test_init_custom_compose_file(self, mock_docker) -> None:
        """Test initialization with custom compose file."""
        with patch.object(ContainerManager, "_check_docker"):
            manager = ContainerManager(compose_file="/custom/docker-compose.yaml")

        assert manager.compose_file == Path("/custom/docker-compose.yaml")


class TestBuild:
    """Tests for container build."""

    def test_build(self) -> None:
        """Test building worker image."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_compose") as mock_compose:
            mock_compose.return_value = MagicMock(returncode=0)

            manager = ContainerManager()
            manager.build()

            mock_compose.assert_called_once()
            call_args = mock_compose.call_args[0]
            assert "build" in call_args

    def test_build_no_cache(self) -> None:
        """Test building with no cache."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_compose") as mock_compose:
            mock_compose.return_value = MagicMock(returncode=0)

            manager = ContainerManager()
            manager.build(no_cache=True)

            call_args = mock_compose.call_args[0]
            assert "--no-cache" in call_args


class TestStartWorker:
    """Tests for starting workers."""

    def test_start_worker(self) -> None:
        """Test starting a worker container."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_docker") as mock_docker, \
             patch.object(ContainerManager, "_run_compose") as mock_compose, \
             patch("time.sleep"):

            # Mock docker ps to return container ID
            mock_docker.return_value = MagicMock(
                returncode=0,
                stdout="abc123def456",
                stderr="",
            )
            mock_compose.return_value = MagicMock(returncode=0)

            manager = ContainerManager()
            info = manager.start_worker(
                worker_id=0,
                feature="test-feature",
                port=49152,
                worktree_path="/tmp/worktree",
                branch="zerg/test/worker-0",
            )

            assert info.worker_id == 0
            assert info.port == 49152
            assert info.status == "running"
            mock_compose.assert_called()

    def test_start_worker_removes_existing(self) -> None:
        """Test starting worker removes existing container."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_docker") as mock_docker, \
             patch.object(ContainerManager, "_run_compose") as mock_compose, \
             patch("time.sleep"):

            mock_docker.return_value = MagicMock(
                returncode=0,
                stdout="abc123",
                stderr="",
            )
            mock_compose.return_value = MagicMock(returncode=0)

            manager = ContainerManager()
            manager.start_worker(0, "test", 49152, "/tmp", "branch")

            # First call should be rm -f for existing container
            first_call = mock_docker.call_args_list[0]
            assert "rm" in first_call[0]
            assert "-f" in first_call[0]


class TestStopWorker:
    """Tests for stopping workers."""

    def test_stop_worker(self) -> None:
        """Test stopping a worker."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_docker") as mock_docker:

            mock_docker.return_value = MagicMock(returncode=0, stdout="", stderr="")

            manager = ContainerManager()
            manager._containers[0] = ContainerInfo(
                container_id="abc123",
                name="zerg-worker-0",
                status="running",
                worker_id=0,
            )

            manager.stop_worker(0)

            assert 0 not in manager._containers

    def test_stop_worker_force(self) -> None:
        """Test force stopping a worker."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_docker") as mock_docker:

            mock_docker.return_value = MagicMock(returncode=0, stdout="", stderr="")

            manager = ContainerManager()
            manager._containers[0] = ContainerInfo(
                container_id="abc123",
                name="zerg-worker-0",
                status="running",
                worker_id=0,
            )

            manager.stop_worker(0, force=True)

            # Should use kill instead of stop
            first_call = mock_docker.call_args_list[0]
            assert "kill" in first_call[0]

    def test_stop_worker_not_found(self) -> None:
        """Test stopping non-existent worker."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_docker"):

            manager = ContainerManager()
            # Should not raise
            manager.stop_worker(99)


class TestStopAll:
    """Tests for stopping all workers."""

    def test_stop_all(self) -> None:
        """Test stopping all workers."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_docker") as mock_docker:

            mock_docker.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )

            manager = ContainerManager()
            manager._containers = {
                0: ContainerInfo("a", "zerg-worker-0", "running", 0),
                1: ContainerInfo("b", "zerg-worker-1", "running", 1),
            }

            count = manager.stop_all()

            assert count >= 2
            assert len(manager._containers) == 0


class TestGetStatus:
    """Tests for getting worker status."""

    def test_get_status_running(self) -> None:
        """Test getting running status."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_docker") as mock_docker:

            mock_docker.return_value = MagicMock(
                returncode=0,
                stdout="running\n",
                stderr="",
            )

            manager = ContainerManager()
            manager._containers[0] = ContainerInfo(
                container_id="abc123",
                name="zerg-worker-0",
                status="running",
                worker_id=0,
            )

            status = manager.get_status(0)

            assert status == WorkerStatus.RUNNING

    def test_get_status_stopped(self) -> None:
        """Test getting stopped status."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_docker") as mock_docker:

            mock_docker.return_value = MagicMock(
                returncode=0,
                stdout="exited\n",
                stderr="",
            )

            manager = ContainerManager()
            manager._containers[0] = ContainerInfo(
                container_id="abc123",
                name="zerg-worker-0",
                status="running",
                worker_id=0,
            )

            status = manager.get_status(0)

            assert status == WorkerStatus.STOPPED

    def test_get_status_not_tracked(self) -> None:
        """Test getting status for untracked worker."""
        with patch.object(ContainerManager, "_check_docker"):
            manager = ContainerManager()

            status = manager.get_status(99)

            assert status == WorkerStatus.STOPPED


class TestGetLogs:
    """Tests for getting container logs."""

    def test_get_logs(self) -> None:
        """Test getting logs."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_docker") as mock_docker:

            mock_docker.return_value = MagicMock(
                returncode=0,
                stdout="Log line 1\nLog line 2\n",
                stderr="",
            )

            manager = ContainerManager()
            manager._containers[0] = ContainerInfo(
                container_id="abc123",
                name="zerg-worker-0",
                status="running",
                worker_id=0,
            )

            logs = manager.get_logs(0)

            assert "Log line 1" in logs
            assert "Log line 2" in logs

    def test_get_logs_not_found(self) -> None:
        """Test getting logs for non-existent worker."""
        with patch.object(ContainerManager, "_check_docker"):
            manager = ContainerManager()

            logs = manager.get_logs(99)

            assert logs == ""


class TestHealthCheck:
    """Tests for health checking."""

    def test_health_check_healthy(self) -> None:
        """Test health check for healthy container."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_docker") as mock_docker:

            mock_docker.return_value = MagicMock(
                returncode=0,
                stdout="running\n",
                stderr="",
            )

            manager = ContainerManager()
            manager._containers[0] = ContainerInfo(
                container_id="abc123",
                name="zerg-worker-0",
                status="running",
                worker_id=0,
            )

            healthy = manager.health_check(0)

            assert healthy is True

    def test_health_check_unhealthy(self) -> None:
        """Test health check for unhealthy container."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_docker") as mock_docker:

            mock_docker.return_value = MagicMock(
                returncode=0,
                stdout="exited\n",
                stderr="",
            )

            manager = ContainerManager()
            manager._containers[0] = ContainerInfo(
                container_id="abc123",
                name="zerg-worker-0",
                status="running",
                worker_id=0,
            )

            healthy = manager.health_check(0)

            assert healthy is False

    def test_health_check_not_found(self) -> None:
        """Test health check for non-existent worker."""
        with patch.object(ContainerManager, "_check_docker"):
            manager = ContainerManager()

            healthy = manager.health_check(99)

            assert healthy is False


class TestExecInWorker:
    """Tests for executing commands in workers."""

    def test_exec_allowed_command(self) -> None:
        """Test executing allowed command."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_docker") as mock_docker:

            mock_docker.return_value = MagicMock(
                returncode=0,
                stdout="output",
                stderr="",
            )

            manager = ContainerManager()
            manager._containers[0] = ContainerInfo(
                container_id="abc123",
                name="zerg-worker-0",
                status="running",
                worker_id=0,
            )

            exit_code, stdout, stderr = manager.exec_in_worker(0, "pytest tests/")

            assert exit_code == 0
            assert stdout == "output"

    def test_exec_blocked_command(self) -> None:
        """Test executing blocked command."""
        with patch.object(ContainerManager, "_check_docker"):
            manager = ContainerManager()
            manager._containers[0] = ContainerInfo(
                container_id="abc123",
                name="zerg-worker-0",
                status="running",
                worker_id=0,
            )

            exit_code, stdout, stderr = manager.exec_in_worker(
                0,
                "rm -rf /; echo pwned",
                validate=True,
            )

            assert exit_code == -1
            assert "validation failed" in stderr.lower()

    def test_exec_shell_metacharacters_blocked(self) -> None:
        """Test shell metacharacters are blocked."""
        with patch.object(ContainerManager, "_check_docker"):
            manager = ContainerManager()
            manager._containers[0] = ContainerInfo(
                container_id="abc123",
                name="zerg-worker-0",
                status="running",
                worker_id=0,
            )

            exit_code, stdout, stderr = manager.exec_in_worker(
                0,
                "echo `whoami`",
                validate=True,
            )

            assert exit_code == -1
            assert "metacharacters" in stderr.lower()

    def test_exec_validation_disabled(self) -> None:
        """Test execution with validation disabled."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_docker") as mock_docker:

            mock_docker.return_value = MagicMock(
                returncode=0,
                stdout="output",
                stderr="",
            )

            manager = ContainerManager()
            manager._containers[0] = ContainerInfo(
                container_id="abc123",
                name="zerg-worker-0",
                status="running",
                worker_id=0,
            )

            exit_code, stdout, stderr = manager.exec_in_worker(
                0,
                "custom_command",
                validate=False,
            )

            assert exit_code == 0

    def test_exec_worker_not_found(self) -> None:
        """Test exec on non-existent worker."""
        with patch.object(ContainerManager, "_check_docker"):
            manager = ContainerManager()

            exit_code, stdout, stderr = manager.exec_in_worker(99, "echo test")

            assert exit_code == -1
            assert "not found" in stderr.lower()


class TestCommandValidation:
    """Tests for command validation."""

    def test_validate_pytest(self) -> None:
        """Test pytest is allowed."""
        with patch.object(ContainerManager, "_check_docker"):
            manager = ContainerManager()

            is_valid, error = manager._validate_exec_command("pytest tests/")

            assert is_valid is True

    def test_validate_git_status(self) -> None:
        """Test git status is allowed."""
        with patch.object(ContainerManager, "_check_docker"):
            manager = ContainerManager()

            is_valid, error = manager._validate_exec_command("git status")

            assert is_valid is True

    def test_validate_empty(self) -> None:
        """Test empty command rejected."""
        with patch.object(ContainerManager, "_check_docker"):
            manager = ContainerManager()

            is_valid, error = manager._validate_exec_command("")

            assert is_valid is False
            assert "empty" in error.lower()

    def test_validate_dangerous_pipe(self) -> None:
        """Test pipe is rejected."""
        with patch.object(ContainerManager, "_check_docker"):
            manager = ContainerManager()

            is_valid, error = manager._validate_exec_command("cat file | bash")

            assert is_valid is False
            assert "metacharacters" in error.lower()


class TestCleanupVolumes:
    """Tests for volume cleanup."""

    def test_cleanup_volumes(self) -> None:
        """Test cleaning up volumes."""
        with patch.object(ContainerManager, "_check_docker"), \
             patch.object(ContainerManager, "_run_docker") as mock_docker:

            mock_docker.return_value = MagicMock(returncode=0)

            manager = ContainerManager()
            manager.cleanup_volumes("test-feature")

            mock_docker.assert_called_once()
            call_args = mock_docker.call_args[0]
            assert "volume" in call_args
            assert "rm" in call_args


class TestGetAllContainers:
    """Tests for getting all containers."""

    def test_get_all_containers(self) -> None:
        """Test getting all tracked containers."""
        with patch.object(ContainerManager, "_check_docker"):
            manager = ContainerManager()
            manager._containers = {
                0: ContainerInfo("a", "worker-0", "running", 0),
                1: ContainerInfo("b", "worker-1", "running", 1),
            }

            containers = manager.get_all_containers()

            assert len(containers) == 2
            assert 0 in containers
            assert 1 in containers

    def test_get_all_containers_returns_copy(self) -> None:
        """Test getting containers returns a copy."""
        with patch.object(ContainerManager, "_check_docker"):
            manager = ContainerManager()
            manager._containers = {
                0: ContainerInfo("a", "worker-0", "running", 0),
            }

            containers = manager.get_all_containers()
            containers[99] = ContainerInfo("x", "worker-99", "running", 99)

            # Original should not be modified
            assert 99 not in manager._containers
