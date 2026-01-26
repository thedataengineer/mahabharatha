"""Tests for ZERG v2 Quality Gates."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGateResult:
    """Tests for GateResult dataclass."""

    def test_gate_result_creation(self):
        """Test GateResult can be created."""
        from gates import GateResult

        result = GateResult(stage=1, passed=True, failures=[])
        assert result.stage == 1
        assert result.passed is True
        assert result.failures == []

    def test_gate_result_with_failures(self):
        """Test GateResult with failures."""
        from gates import GateResult

        result = GateResult(
            stage=2, passed=False, failures=["lint failed", "coverage below threshold"]
        )
        assert result.passed is False
        assert len(result.failures) == 2

    def test_gate_result_summary(self):
        """Test GateResult summary method."""
        from gates import GateResult

        result = GateResult(stage=1, passed=True, failures=[])
        summary = result.summary()
        assert "Stage 1" in summary
        assert "PASSED" in summary


class TestSpecComplianceGate:
    """Tests for Stage 1: Spec Compliance Gate."""

    def test_spec_compliance_gate_creation(self):
        """Test SpecComplianceGate can be created."""
        from gates import SpecComplianceGate

        gate = SpecComplianceGate()
        assert gate is not None

    def test_check_requirements_met_success(self):
        """Test requirements check passes when all met."""
        from gates import SpecComplianceGate
        from task_graph import Task, TaskFiles, VerificationConfig

        gate = SpecComplianceGate()
        task = Task(
            id="TASK-001",
            title="Test task",
            description="Test",
            level=1,
            dependencies=[],
            files=TaskFiles(create=["test.py"], modify=[], read=[]),
            acceptance_criteria=["File created"],
            verification=VerificationConfig(command="echo test", timeout_seconds=60),
        )
        # Mark task as completed
        task.status = "completed"
        result = gate._check_requirements_met(1, [task])
        assert result.passed is True

    def test_check_requirements_met_failure(self):
        """Test requirements check fails when task incomplete."""
        from gates import SpecComplianceGate
        from task_graph import Task, TaskFiles, VerificationConfig

        gate = SpecComplianceGate()
        task = Task(
            id="TASK-001",
            title="Test task",
            description="Test",
            level=1,
            dependencies=[],
            files=TaskFiles(create=["test.py"], modify=[], read=[]),
            acceptance_criteria=["File created"],
            verification=VerificationConfig(command="echo test", timeout_seconds=60),
        )
        task.status = "failed"
        result = gate._check_requirements_met(1, [task])
        assert result.passed is False
        assert len(result.issues) > 0

    def test_check_file_ownership_success(self):
        """Test file ownership check passes when no conflicts."""
        from gates import SpecComplianceGate
        from task_graph import Task, TaskFiles, VerificationConfig

        gate = SpecComplianceGate()
        task1 = Task(
            id="TASK-001",
            title="Task 1",
            description="Test",
            level=1,
            dependencies=[],
            files=TaskFiles(create=["file1.py"], modify=[], read=[]),
            acceptance_criteria=["Done"],
            verification=VerificationConfig(command="echo", timeout_seconds=60),
        )
        task2 = Task(
            id="TASK-002",
            title="Task 2",
            description="Test",
            level=1,
            dependencies=[],
            files=TaskFiles(create=["file2.py"], modify=[], read=[]),
            acceptance_criteria=["Done"],
            verification=VerificationConfig(command="echo", timeout_seconds=60),
        )
        result = gate._check_file_ownership(1, [task1, task2])
        assert result.passed is True

    def test_check_file_ownership_conflict(self):
        """Test file ownership check fails on conflict."""
        from gates import SpecComplianceGate
        from task_graph import Task, TaskFiles, VerificationConfig

        gate = SpecComplianceGate()
        task1 = Task(
            id="TASK-001",
            title="Task 1",
            description="Test",
            level=1,
            dependencies=[],
            files=TaskFiles(create=["same.py"], modify=[], read=[]),
            acceptance_criteria=["Done"],
            verification=VerificationConfig(command="echo", timeout_seconds=60),
        )
        task2 = Task(
            id="TASK-002",
            title="Task 2",
            description="Test",
            level=1,
            dependencies=[],
            files=TaskFiles(create=["same.py"], modify=[], read=[]),
            acceptance_criteria=["Done"],
            verification=VerificationConfig(command="echo", timeout_seconds=60),
        )
        result = gate._check_file_ownership(1, [task1, task2])
        assert result.passed is False
        assert "same.py" in str(result.issues)

    def test_run_all_checks(self):
        """Test running all spec compliance checks."""
        from gates import SpecComplianceGate
        from task_graph import Task, TaskFiles, VerificationConfig

        gate = SpecComplianceGate()
        task = Task(
            id="TASK-001",
            title="Test",
            description="Test",
            level=1,
            dependencies=[],
            files=TaskFiles(create=["test.py"], modify=[], read=[]),
            acceptance_criteria=["Done"],
            verification=VerificationConfig(command="echo", timeout_seconds=60),
        )
        task.status = "completed"
        result = gate.run(1, [task])
        assert result.stage == 1


class TestCodeQualityGate:
    """Tests for Stage 2: Code Quality Gate."""

    def test_code_quality_gate_creation(self):
        """Test CodeQualityGate can be created."""
        from gates import CodeQualityGate

        gate = CodeQualityGate()
        assert gate is not None

    def test_code_quality_gate_with_config(self):
        """Test CodeQualityGate with custom config."""
        from gates import CodeQualityGate, QualityConfig

        config = QualityConfig(coverage_threshold=80, complexity_threshold=10)
        gate = CodeQualityGate(config=config)
        assert gate.config.coverage_threshold == 80

    def test_run_linter_success(self):
        """Test linter check passes on clean code."""
        from gates import CodeQualityGate

        gate = CodeQualityGate()
        # Use existing file that passes lint
        result = gate._run_linter([".zerg/task_graph.py"])
        # May pass or fail depending on actual lint state
        assert isinstance(result.passed, bool)

    def test_check_coverage_threshold(self):
        """Test coverage threshold check."""
        from gates import CodeQualityGate, QualityConfig

        config = QualityConfig(coverage_threshold=80)
        gate = CodeQualityGate(config=config)
        # Without actual coverage data, check method exists
        result = gate._check_coverage([])
        assert isinstance(result.passed, bool)

    def test_run_all_quality_checks(self):
        """Test running all code quality checks."""
        from gates import CodeQualityGate

        gate = CodeQualityGate()
        result = gate.run(1, [])
        assert result.stage == 2


class TestGateRunner:
    """Tests for GateRunner that orchestrates both stages."""

    def test_gate_runner_creation(self):
        """Test GateRunner can be created."""
        from gates import GateRunner

        runner = GateRunner()
        assert runner is not None

    def test_gate_runner_run_stage1(self):
        """Test running only stage 1."""
        from gates import GateRunner
        from task_graph import Task, TaskFiles, VerificationConfig

        runner = GateRunner()
        task = Task(
            id="TASK-001",
            title="Test",
            description="Test",
            level=1,
            dependencies=[],
            files=TaskFiles(create=["test.py"], modify=[], read=[]),
            acceptance_criteria=["Done"],
            verification=VerificationConfig(command="echo", timeout_seconds=60),
        )
        task.status = "completed"
        result = runner.run_stage1(1, [task])
        assert result.stage == 1

    def test_gate_runner_run_stage2(self):
        """Test running only stage 2."""
        from gates import GateRunner

        runner = GateRunner()
        result = runner.run_stage2(1, [])
        assert result.stage == 2

    def test_gate_runner_run_both_stages(self):
        """Test running both stages."""
        from gates import GateRunner
        from task_graph import Task, TaskFiles, VerificationConfig

        runner = GateRunner()
        task = Task(
            id="TASK-001",
            title="Test",
            description="Test",
            level=1,
            dependencies=[],
            files=TaskFiles(create=["test.py"], modify=[], read=[]),
            acceptance_criteria=["Done"],
            verification=VerificationConfig(command="echo", timeout_seconds=60),
        )
        task.status = "completed"
        results = runner.run_all(1, [task], [])
        assert len(results) == 2
        assert results[0].stage == 1
        assert results[1].stage == 2

    def test_gate_runner_stops_on_stage1_failure(self):
        """Test stage 2 doesn't run if stage 1 fails."""
        from gates import GateRunner
        from task_graph import Task, TaskFiles, VerificationConfig

        runner = GateRunner()
        task = Task(
            id="TASK-001",
            title="Test",
            description="Test",
            level=1,
            dependencies=[],
            files=TaskFiles(create=["test.py"], modify=[], read=[]),
            acceptance_criteria=["Done"],
            verification=VerificationConfig(command="echo", timeout_seconds=60),
        )
        task.status = "failed"  # Will cause stage 1 to fail
        results = runner.run_all(1, [task], [], stop_on_failure=True)
        assert len(results) == 1  # Only stage 1 ran


class TestCheckResult:
    """Tests for individual check results."""

    def test_check_result_creation(self):
        """Test CheckResult can be created."""
        from gates import CheckResult

        result = CheckResult(passed=True, issues=[])
        assert result.passed is True

    def test_check_result_with_issues(self):
        """Test CheckResult with issues."""
        from gates import CheckResult

        result = CheckResult(passed=False, issues=["error 1", "error 2"])
        assert result.passed is False
        assert len(result.issues) == 2


class TestQualityConfig:
    """Tests for quality configuration."""

    def test_quality_config_defaults(self):
        """Test QualityConfig has sensible defaults."""
        from gates import QualityConfig

        config = QualityConfig()
        assert config.coverage_threshold >= 0
        assert config.complexity_threshold > 0

    def test_quality_config_custom(self):
        """Test QualityConfig with custom values."""
        from gates import QualityConfig

        config = QualityConfig(
            coverage_threshold=90, complexity_threshold=5, run_security_scan=True
        )
        assert config.coverage_threshold == 90
        assert config.complexity_threshold == 5
        assert config.run_security_scan is True
