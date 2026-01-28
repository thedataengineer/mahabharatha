"""ZERG v2 Test Runner - Test generation, execution, and coverage analysis."""

import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import secure command executor
sys.path.insert(0, str(Path(__file__).parent.parent))
from zerg.command_executor import CommandExecutor, CommandValidationError


class Framework(Enum):
    """Supported test frameworks."""

    PYTEST = "pytest"
    JEST = "jest"
    CARGO = "cargo"
    GO = "go"
    MOCHA = "mocha"
    VITEST = "vitest"


# Backward compat aliases (will be removed in v3)
TestFramework = Framework


@dataclass
class RunConfig:
    """Configuration for test execution."""

    parallel: bool = True
    coverage: bool = False
    watch: bool = False
    workers: int = 4
    timeout_seconds: int = 300
    verbose: bool = False
    filter: str = ""


# Backward compat aliases (will be removed in v3)
TestConfig = RunConfig


@dataclass
class RunResult:
    """Result of test execution."""

    total: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float = 0.0
    coverage_percentage: float | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if all tests passed."""
        return self.failed == 0

    @property
    def pass_percentage(self) -> float:
        """Calculate pass percentage."""
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100


# Backward compat aliases (will be removed in v3)
TestResult = RunResult


@dataclass
class CoverageReport:
    """Coverage analysis report."""

    total_lines: int
    covered_lines: int
    percentage: float
    files: dict[str, float] = field(default_factory=dict)

    def meets_threshold(self, threshold: int) -> bool:
        """Check if coverage meets threshold."""
        return self.percentage >= threshold


class FrameworkDetector:
    """Detect test frameworks from project structure."""

    FRAMEWORK_MARKERS = {
        Framework.PYTEST: ["pytest.ini", "pyproject.toml", "conftest.py"],
        Framework.JEST: ["jest.config.js", "jest.config.ts", "package.json"],
        Framework.CARGO: ["Cargo.toml"],
        Framework.GO: ["go.mod"],
        Framework.MOCHA: [".mocharc.js", ".mocharc.json"],
        Framework.VITEST: ["vitest.config.ts", "vitest.config.js"],
    }

    def detect(self, project_path: Path) -> list[TestFramework]:
        """Detect test frameworks in project.

        Args:
            project_path: Path to project root

        Returns:
            List of detected frameworks
        """
        detected = []

        for framework, markers in self.FRAMEWORK_MARKERS.items():
            for marker in markers:
                if (project_path / marker).exists():
                    if framework not in detected:
                        detected.append(framework)
                    break

        # Check package.json for JS frameworks
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    pkg = json.load(f)
                    deps = {
                        **pkg.get("dependencies", {}),
                        **pkg.get("devDependencies", {}),
                    }
                    if "jest" in deps and Framework.JEST not in detected:
                        detected.append(Framework.JEST)
                    if "vitest" in deps and Framework.VITEST not in detected:
                        detected.append(Framework.VITEST)
                    if "mocha" in deps and Framework.MOCHA not in detected:
                        detected.append(Framework.MOCHA)
            except (json.JSONDecodeError, OSError):
                pass

        return detected


class Runner:
    """Execute tests with various frameworks."""

    COMMANDS = {
        Framework.PYTEST: "python -m pytest",
        Framework.JEST: "npx jest",
        Framework.CARGO: "cargo test",
        Framework.GO: "go test ./...",
        Framework.MOCHA: "npx mocha",
        Framework.VITEST: "npx vitest run",
    }

    def __init__(self, config: RunConfig | None = None):
        """Initialize test runner."""
        self.config = config or RunConfig()

    def _get_executor(self, cwd: str = ".") -> CommandExecutor:
        """Get command executor for test execution."""
        return CommandExecutor(
            working_dir=Path(cwd),
            allow_unlisted=True,  # Allow test commands
            timeout=self.config.timeout_seconds,
        )

    def get_command(self, framework: Framework) -> str:
        """Get test command for framework.

        Args:
            framework: Test framework to use

        Returns:
            Command string
        """
        base_cmd = self.COMMANDS.get(framework, "pytest")

        if framework == Framework.PYTEST:
            args = []
            if self.config.coverage:
                args.append("--cov")
            if self.config.parallel and self.config.workers > 1:
                args.append(f"-n {self.config.workers}")
            if self.config.verbose:
                args.append("-v")
            if self.config.filter:
                args.append(f"-k '{self.config.filter}'")
            return f"{base_cmd} {' '.join(args)}".strip()

        elif framework == Framework.JEST:
            args = []
            if self.config.coverage:
                args.append("--coverage")
            if self.config.parallel:
                args.append(f"--maxWorkers={self.config.workers}")
            if self.config.watch:
                args.append("--watch")
            return f"{base_cmd} {' '.join(args)}".strip()

        elif framework == Framework.CARGO:
            args = []
            if self.config.parallel:
                args.append(f"-- --test-threads={self.config.workers}")
            return f"{base_cmd} {' '.join(args)}".strip()

        return base_cmd

    def run(
        self, framework: Framework, path: str = "."
    ) -> RunResult:
        """Run tests and return results.

        Args:
            framework: Test framework to use
            path: Path to test directory

        Returns:
            TestResult with execution details
        """
        cmd = self.get_command(framework)

        try:
            # Use secure command executor - no shell=True
            executor = self._get_executor(path)
            result = executor.execute(cmd, timeout=self.config.timeout_seconds)

            # Parse output based on framework
            return self._parse_output(framework, result.stdout, result.exit_code)

        except CommandValidationError as e:
            return RunResult(
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=[f"Command validation failed: {e}"],
            )
        except Exception as e:
            return RunResult(
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=[f"Test execution error: {e}"],
            )

    def _parse_output(
        self, framework: Framework, output: str, returncode: int
    ) -> RunResult:
        """Parse test output to extract results."""
        # Basic parsing - real implementation would be framework-specific
        if returncode == 0:
            return RunResult(total=1, passed=1, failed=0, skipped=0)
        else:
            return RunResult(
                total=1, passed=0, failed=1, skipped=0, errors=[output[:500]]
            )


# Backward compat alias (will be removed in v3)
TestRunner = Runner


class Command:
    """Main test command orchestrator."""

    def __init__(self, config: RunConfig | None = None):
        """Initialize test command."""
        self.config = config or RunConfig()
        self.detector = FrameworkDetector()
        self.runner = Runner(config=self.config)

    def supported_frameworks(self) -> list[str]:
        """Return list of supported frameworks."""
        return [f.value for f in Framework]

    def run(
        self,
        framework: Framework | None = None,
        path: str = ".",
        dry_run: bool = False,
    ) -> RunResult:
        """Run tests.

        Args:
            framework: Framework to use (auto-detect if None)
            path: Path to test directory
            dry_run: If True, don't actually run tests

        Returns:
            TestResult with execution details
        """
        if dry_run:
            return RunResult(total=0, passed=0, failed=0, skipped=0)

        if framework is None:
            detected = self.detector.detect(Path(path))
            framework = detected[0] if detected else Framework.PYTEST

        return self.runner.run(framework, path)

    def format_result(self, result: RunResult, format: str = "text") -> str:
        """Format test result.

        Args:
            result: Test result to format
            format: Output format (text or json)

        Returns:
            Formatted string
        """
        if format == "json":
            return json.dumps(
                {
                    "total": result.total,
                    "passed": result.passed,
                    "failed": result.failed,
                    "skipped": result.skipped,
                    "success": result.success,
                    "pass_percentage": result.pass_percentage,
                    "duration_seconds": result.duration_seconds,
                    "errors": result.errors,
                },
                indent=2,
            )

        lines = [
            "Test Results",
            "=" * 40,
            f"Total: {result.total}",
            f"Passed: {result.passed}",
            f"Failed: {result.failed}",
            f"Skipped: {result.skipped}",
            "",
            f"Pass Rate: {result.pass_percentage:.1f}%",
        ]
        if result.duration_seconds:
            lines.append(f"Duration: {result.duration_seconds:.2f}s")
        if result.errors:
            lines.append("")
            lines.append("Errors:")
            for error in result.errors[:5]:
                lines.append(f"  - {error[:100]}")

        return "\n".join(lines)


# Backward compat alias (will be removed in v3)
TestCommand = Command


class StubGenerator:
    """Generate test stubs for uncovered code."""

    TEMPLATES = {
        "function": '''def test_{name}():
    """Test {name} function."""
    # TODO: Implement test
    result = {name}()
    assert result is not None
''',
        "class": '''class Test{name}:
    """Tests for {name} class."""

    def test_{name}_creation(self):
        """Test {name} can be created."""
        instance = {name}()
        assert instance is not None
''',
        "method": '''def test_{class_name}_{name}(self):
    """Test {class_name}.{name} method."""
    # TODO: Implement test
    instance = {class_name}()
    result = instance.{name}()
    assert result is not None
''',
    }

    def generate_stub(
        self, name: str, kind: str = "function", class_name: str = ""
    ) -> str:
        """Generate test stub.

        Args:
            name: Name of function/class/method
            kind: Type of code element
            class_name: Parent class name for methods

        Returns:
            Test stub code
        """
        template = self.TEMPLATES.get(kind, self.TEMPLATES["function"])
        return template.format(name=name, class_name=class_name)


# Backward compat alias (will be removed in v3)
TestStubGenerator = StubGenerator


__all__ = [
    # New names
    "Framework",
    "RunConfig",
    "RunResult",
    "CoverageReport",
    "FrameworkDetector",
    "Runner",
    "Command",
    "StubGenerator",
    # Backward compat aliases (will be removed in v3)
    "TestFramework",
    "TestConfig",
    "TestResult",
    "TestRunner",
    "TestCommand",
    "TestStubGenerator",
]
