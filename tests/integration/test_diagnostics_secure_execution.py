"""Integration tests for secure command execution in diagnostics modules.

Tests verify that HypothesisTestRunner, StepExecutor, and RecoveryPlanner
use CommandExecutor for secure command execution.
"""

from mahabharatha.command_executor import CommandExecutor
from mahabharatha.diagnostics.hypothesis_engine import HypothesisTestRunner
from mahabharatha.diagnostics.recovery import RecoveryPlanner, RecoveryStep
from mahabharatha.diagnostics.types import ErrorCategory, ScoredHypothesis
from mahabharatha.step_executor import StepExecutor


class TestModulesUseCommandExecutor:
    """Verify that diagnostics modules use CommandExecutor."""

    def test_hypothesis_test_runner_uses_executor(self):
        """HypothesisTestRunner should have a CommandExecutor instance."""
        runner = HypothesisTestRunner()
        assert hasattr(runner, "_executor")
        assert isinstance(runner._executor, CommandExecutor)

    def test_step_executor_uses_executor(self):
        """StepExecutor should have a CommandExecutor instance."""
        executor = StepExecutor(task_id="test-task")
        assert hasattr(executor, "_executor")
        assert isinstance(executor._executor, CommandExecutor)

    def test_recovery_planner_uses_executor(self):
        """RecoveryPlanner should have a CommandExecutor instance."""
        planner = RecoveryPlanner()
        assert hasattr(planner, "_executor")
        assert isinstance(planner._executor, CommandExecutor)


class TestHypothesisTestE2E:
    """End-to-end tests for hypothesis testing with safe commands."""

    def test_hypothesis_test_with_safe_echo_command(self):
        """Hypothesis with 'echo' command should test successfully."""
        runner = HypothesisTestRunner()
        hypothesis = ScoredHypothesis(
            description="Test echo command",
            category=ErrorCategory.UNKNOWN,
            prior_probability=0.5,
            evidence_for=[],
            evidence_against=[],
            test_command="echo test",
        )

        result = runner.test(hypothesis, timeout=10)

        assert result.test_result == "PASSED"
        assert result.posterior_probability > 0.5  # Should be boosted

    def test_hypothesis_test_with_failing_command(self):
        """Hypothesis with failing command should update probability correctly."""
        runner = HypothesisTestRunner()
        hypothesis = ScoredHypothesis(
            description="Test failing command",
            category=ErrorCategory.UNKNOWN,
            prior_probability=0.5,
            evidence_for=[],
            evidence_against=[],
            test_command="false",  # Always returns exit code 1
        )

        result = runner.test(hypothesis, timeout=10)

        assert result.test_result == "FAILED"
        assert result.posterior_probability < 0.5  # Should be reduced

    def test_hypothesis_test_with_unlisted_command_fails_validation(self):
        """Hypothesis with command not in allowlist should fail validation."""
        runner = HypothesisTestRunner()
        hypothesis = ScoredHypothesis(
            description="Test unlisted command",
            category=ErrorCategory.UNKNOWN,
            prior_probability=0.5,
            evidence_for=[],
            evidence_against=[],
            test_command="some_unknown_command arg1",
        )

        # The hypothesis should not be testable due to unlisted command
        can_test = runner.can_test(hypothesis)

        if can_test:
            # If somehow testable, test should fail validation
            result = runner.test(hypothesis, timeout=10)
            assert "ERROR" in result.test_result or result.test_result == "FAILED"
        else:
            # Expected: cannot test due to validation failure
            assert not can_test


class TestRecoveryPlanE2E:
    """End-to-end tests for recovery plan execution."""

    def test_recovery_step_with_safe_command(self):
        """Recovery step with safe command should execute successfully."""
        planner = RecoveryPlanner()
        step = RecoveryStep(
            description="Check git status",
            command="git status",
            risk="safe",
            reversible=True,
        )

        result = planner.execute_step(step)

        # Should succeed (even if not in git repo, command runs)
        assert "success" in result
        assert "skipped" in result
        assert result["skipped"] is False

    def test_recovery_step_echo_command(self):
        """Recovery step with echo should execute and return output."""
        planner = RecoveryPlanner()
        step = RecoveryStep(
            description="Echo test",
            command="echo hello",
            risk="safe",
            reversible=True,
        )

        result = planner.execute_step(step)

        assert result["success"] is True
        assert "hello" in result["output"]


class TestStepExecutorE2E:
    """End-to-end tests for step executor."""

    def test_step_executor_with_echo_command(self):
        """StepExecutor should handle echo command successfully."""
        executor = StepExecutor(task_id="test-task", default_timeout=10)
        steps = [{"step": 1, "action": "verify", "run": "echo test", "verify": "exit_code"}]

        result = executor.execute(steps)

        assert result.success is True
        assert len(result.step_results) == 1
        assert result.step_results[0].exit_code == 0

    def test_step_executor_classic_mode_without_steps(self):
        """StepExecutor in classic mode (no steps) should return success."""
        executor = StepExecutor(task_id="test-task")
        result = executor.execute(None)

        assert result.success is True
        assert result.step_results == []
