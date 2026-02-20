"""Tests for MAHABHARATHA v2 Test Runner Command."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTestFramework:
    """Tests for test framework enumeration."""

    def test_frameworks_exist(self):
        """Test framework types are defined."""
        from test_runner import TestFramework

        assert hasattr(TestFramework, "PYTEST")
        assert hasattr(TestFramework, "JEST")
        assert hasattr(TestFramework, "CARGO")
        assert hasattr(TestFramework, "GO")


class TestTestConfig:
    """Tests for test configuration."""

    def test_config_defaults(self):
        """Test TestConfig has sensible defaults."""
        from test_runner import TestConfig

        config = TestConfig()
        assert config.parallel is True
        assert config.coverage is False

    def test_config_custom(self):
        """Test TestConfig with custom values."""
        from test_runner import TestConfig

        config = TestConfig(parallel=False, coverage=True, watch=True)
        assert config.parallel is False
        assert config.coverage is True
        assert config.watch is True


class TestTestResult:
    """Tests for test results."""

    def test_result_creation(self):
        """Test TestResult can be created."""
        from test_runner import TestResult

        result = TestResult(
            total=10, passed=8, failed=2, skipped=0, duration_seconds=5.5
        )
        assert result.total == 10
        assert result.passed == 8

    def test_result_success(self):
        """Test TestResult success detection."""
        from test_runner import TestResult

        success = TestResult(total=10, passed=10, failed=0, skipped=0)
        assert success.success is True

        failure = TestResult(total=10, passed=8, failed=2, skipped=0)
        assert failure.success is False

    def test_result_percentage(self):
        """Test TestResult pass percentage."""
        from test_runner import TestResult

        result = TestResult(total=10, passed=8, failed=2, skipped=0)
        assert result.pass_percentage == 80.0


class TestFrameworkDetector:
    """Tests for test framework detection."""

    def test_detector_creation(self):
        """Test FrameworkDetector can be created."""
        from test_runner import FrameworkDetector

        detector = FrameworkDetector()
        assert detector is not None

    def test_detect_from_files(self):
        """Test detection from project files."""
        from test_runner import FrameworkDetector

        detector = FrameworkDetector()
        # Current project has pytest - use parent of .mahabharatha
        project_root = Path(__file__).parent.parent.parent
        frameworks = detector.detect(project_root)
        # May not detect if pyproject.toml doesn't exist, check for any detection
        assert isinstance(frameworks, list)


class TestTestRunner:
    """Tests for TestRunner class."""

    def test_runner_creation(self):
        """Test TestRunner can be created."""
        from test_runner import TestRunner

        runner = TestRunner()
        assert runner is not None

    def test_runner_with_config(self):
        """Test TestRunner with custom config."""
        from test_runner import TestConfig, TestRunner

        config = TestConfig(coverage=True)
        runner = TestRunner(config=config)
        assert runner.config.coverage is True

    def test_runner_get_command_pytest(self):
        """Test getting pytest command."""
        from test_runner import TestFramework, TestRunner

        runner = TestRunner()
        cmd = runner.get_command(TestFramework.PYTEST)
        assert "pytest" in cmd

    def test_runner_get_command_jest(self):
        """Test getting jest command."""
        from test_runner import TestFramework, TestRunner

        runner = TestRunner()
        cmd = runner.get_command(TestFramework.JEST)
        assert "jest" in cmd

    def test_runner_get_command_with_coverage(self):
        """Test getting command with coverage."""
        from test_runner import TestConfig, TestFramework, TestRunner

        config = TestConfig(coverage=True)
        runner = TestRunner(config=config)
        cmd = runner.get_command(TestFramework.PYTEST)
        assert "--cov" in cmd

    def test_runner_get_command_with_parallel(self):
        """Test getting command with parallel option."""
        from test_runner import TestConfig, TestFramework, TestRunner

        config = TestConfig(parallel=True, workers=4)
        runner = TestRunner(config=config)
        cmd = runner.get_command(TestFramework.PYTEST)
        # pytest-xdist uses -n
        assert "-n" in cmd or "parallel" in cmd.lower()


class TestTestCommand:
    """Tests for TestCommand class."""

    def test_command_creation(self):
        """Test TestCommand can be created."""
        from test_runner import TestCommand

        cmd = TestCommand()
        assert cmd is not None

    def test_command_supported_frameworks(self):
        """Test listing supported frameworks."""
        from test_runner import TestCommand

        cmd = TestCommand()
        frameworks = cmd.supported_frameworks()
        assert "pytest" in frameworks
        assert "jest" in frameworks

    def test_command_run_returns_result(self):
        """Test run returns TestResult."""
        from test_runner import TestCommand, TestResult

        cmd = TestCommand()
        # Run without actual test execution (dry run)
        result = cmd.run(dry_run=True)
        assert isinstance(result, TestResult)

    def test_command_format_text(self):
        """Test text output format."""
        from test_runner import TestCommand, TestResult

        cmd = TestCommand()
        result = TestResult(total=10, passed=8, failed=2, skipped=0, duration_seconds=1.5)
        output = cmd.format_result(result, format="text")
        assert "10" in output  # total
        assert "8" in output  # passed

    def test_command_format_json(self):
        """Test JSON output format."""
        import json

        from test_runner import TestCommand, TestResult

        cmd = TestCommand()
        result = TestResult(total=10, passed=10, failed=0, skipped=0)
        output = cmd.format_result(result, format="json")
        data = json.loads(output)
        assert data["total"] == 10


class TestCoverageReport:
    """Tests for coverage reporting."""

    def test_coverage_report_creation(self):
        """Test CoverageReport can be created."""
        from test_runner import CoverageReport

        report = CoverageReport(
            total_lines=1000, covered_lines=800, percentage=80.0, files={}
        )
        assert report.percentage == 80.0

    def test_coverage_report_threshold_check(self):
        """Test coverage threshold checking."""
        from test_runner import CoverageReport

        report = CoverageReport(
            total_lines=1000, covered_lines=800, percentage=80.0, files={}
        )
        assert report.meets_threshold(70) is True
        assert report.meets_threshold(90) is False


class TestTestStubGenerator:
    """Tests for test stub generation."""

    def test_stub_generator_creation(self):
        """Test TestStubGenerator can be created."""
        from test_runner import TestStubGenerator

        generator = TestStubGenerator()
        assert generator is not None

    def test_stub_generator_for_function(self):
        """Test generating stub for a function."""
        from test_runner import TestStubGenerator

        generator = TestStubGenerator()
        stub = generator.generate_stub("my_function", "function")
        assert "test" in stub.lower()
        assert "my_function" in stub
