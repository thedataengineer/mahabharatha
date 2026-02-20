"""Tests for MAHABHARATHA v2 Analyze Command."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAnalyzeConfig:
    """Tests for analysis configuration."""

    def test_analyze_config_defaults(self):
        """Test AnalyzeConfig has sensible defaults."""
        from analyze import AnalyzeConfig

        config = AnalyzeConfig()
        assert config.complexity_threshold > 0
        assert config.coverage_threshold >= 0

    def test_analyze_config_custom(self):
        """Test AnalyzeConfig with custom values."""
        from analyze import AnalyzeConfig

        config = AnalyzeConfig(complexity_threshold=15, coverage_threshold=90)
        assert config.complexity_threshold == 15
        assert config.coverage_threshold == 90


class TestCheckType:
    """Tests for check type enumeration."""

    def test_check_types_exist(self):
        """Test check types are defined."""
        from analyze import CheckType

        assert hasattr(CheckType, "LINT")
        assert hasattr(CheckType, "COMPLEXITY")
        assert hasattr(CheckType, "COVERAGE")
        assert hasattr(CheckType, "SECURITY")


class TestAnalysisResult:
    """Tests for analysis results."""

    def test_analysis_result_creation(self):
        """Test AnalysisResult can be created."""
        from analyze import AnalysisResult, CheckType

        result = AnalysisResult(
            check_type=CheckType.LINT, passed=True, issues=[], score=100.0
        )
        assert result.check_type == CheckType.LINT
        assert result.passed is True
        assert result.score == 100.0

    def test_analysis_result_with_issues(self):
        """Test AnalysisResult with issues."""
        from analyze import AnalysisResult, CheckType

        result = AnalysisResult(
            check_type=CheckType.LINT,
            passed=False,
            issues=["error 1", "error 2"],
            score=70.0,
        )
        assert result.passed is False
        assert len(result.issues) == 2

    def test_analysis_result_summary(self):
        """Test AnalysisResult summary generation."""
        from analyze import AnalysisResult, CheckType

        result = AnalysisResult(
            check_type=CheckType.COMPLEXITY, passed=True, issues=[], score=85.0
        )
        summary = result.summary()
        assert "COMPLEXITY" in summary
        assert "PASSED" in summary


class TestLintChecker:
    """Tests for lint checker."""

    def test_lint_checker_creation(self):
        """Test LintChecker can be created."""
        from analyze import LintChecker

        checker = LintChecker()
        assert checker is not None

    def test_lint_checker_name(self):
        """Test LintChecker has correct name."""
        from analyze import LintChecker

        checker = LintChecker()
        assert checker.name == "lint"

    def test_lint_checker_supported_languages(self):
        """Test LintChecker supports common languages."""
        from analyze import LintChecker

        checker = LintChecker()
        languages = checker.supported_languages()
        assert "python" in languages


class TestComplexityChecker:
    """Tests for complexity checker."""

    def test_complexity_checker_creation(self):
        """Test ComplexityChecker can be created."""
        from analyze import ComplexityChecker

        checker = ComplexityChecker()
        assert checker is not None

    def test_complexity_checker_name(self):
        """Test ComplexityChecker has correct name."""
        from analyze import ComplexityChecker

        checker = ComplexityChecker()
        assert checker.name == "complexity"

    def test_complexity_checker_threshold(self):
        """Test ComplexityChecker with custom threshold."""
        from analyze import ComplexityChecker

        checker = ComplexityChecker(threshold=15)
        assert checker.threshold == 15


class TestCoverageChecker:
    """Tests for coverage checker."""

    def test_coverage_checker_creation(self):
        """Test CoverageChecker can be created."""
        from analyze import CoverageChecker

        checker = CoverageChecker()
        assert checker is not None

    def test_coverage_checker_name(self):
        """Test CoverageChecker has correct name."""
        from analyze import CoverageChecker

        checker = CoverageChecker()
        assert checker.name == "coverage"

    def test_coverage_checker_threshold(self):
        """Test CoverageChecker with custom threshold."""
        from analyze import CoverageChecker

        checker = CoverageChecker(threshold=80)
        assert checker.threshold == 80


class TestSecurityChecker:
    """Tests for security checker."""

    def test_security_checker_creation(self):
        """Test SecurityChecker can be created."""
        from analyze import SecurityChecker

        checker = SecurityChecker()
        assert checker is not None

    def test_security_checker_name(self):
        """Test SecurityChecker has correct name."""
        from analyze import SecurityChecker

        checker = SecurityChecker()
        assert checker.name == "security"


class TestAnalyzeCommand:
    """Tests for AnalyzeCommand class."""

    def test_analyze_command_creation(self):
        """Test AnalyzeCommand can be created."""
        from analyze import AnalyzeCommand

        cmd = AnalyzeCommand()
        assert cmd is not None

    def test_analyze_command_supported_checks(self):
        """Test AnalyzeCommand lists supported checks."""
        from analyze import AnalyzeCommand

        cmd = AnalyzeCommand()
        checks = cmd.supported_checks()
        assert "lint" in checks
        assert "complexity" in checks
        assert "coverage" in checks
        assert "security" in checks

    def test_analyze_command_run_single_check(self):
        """Test running a single check type."""
        from analyze import AnalyzeCommand

        cmd = AnalyzeCommand()
        results = cmd.run(checks=["lint"], files=[])
        assert len(results) == 1
        assert results[0].check_type.value == "lint"

    def test_analyze_command_run_all_checks(self):
        """Test running all checks."""
        from analyze import AnalyzeCommand

        cmd = AnalyzeCommand()
        results = cmd.run(checks=["all"], files=[])
        assert len(results) == 4  # lint, complexity, coverage, security

    def test_analyze_command_format_text(self):
        """Test text output format."""
        from analyze import AnalysisResult, AnalyzeCommand, CheckType

        cmd = AnalyzeCommand()
        results = [AnalysisResult(CheckType.LINT, True, [], 100.0)]
        output = cmd.format_results(results, format="text")
        assert "lint" in output.lower()

    def test_analyze_command_format_json(self):
        """Test JSON output format."""
        import json

        from analyze import AnalysisResult, AnalyzeCommand, CheckType

        cmd = AnalyzeCommand()
        results = [AnalysisResult(CheckType.LINT, True, [], 100.0)]
        output = cmd.format_results(results, format="json")
        data = json.loads(output)
        assert "results" in data

    def test_analyze_command_overall_status(self):
        """Test overall status calculation."""
        from analyze import AnalysisResult, AnalyzeCommand, CheckType

        cmd = AnalyzeCommand()
        results = [
            AnalysisResult(CheckType.LINT, True, [], 100.0),
            AnalysisResult(CheckType.COMPLEXITY, False, ["too complex"], 60.0),
        ]
        assert cmd.overall_passed(results) is False

    def test_analyze_command_all_passed(self):
        """Test overall status when all pass."""
        from analyze import AnalysisResult, AnalyzeCommand, CheckType

        cmd = AnalyzeCommand()
        results = [
            AnalysisResult(CheckType.LINT, True, [], 100.0),
            AnalysisResult(CheckType.COMPLEXITY, True, [], 85.0),
        ]
        assert cmd.overall_passed(results) is True


class TestOutputFormats:
    """Tests for output format handling."""

    def test_sarif_format(self):
        """Test SARIF output format for integration."""
        from analyze import AnalysisResult, AnalyzeCommand, CheckType

        cmd = AnalyzeCommand()
        results = [
            AnalysisResult(CheckType.LINT, False, ["error at line 10"], 80.0)
        ]
        output = cmd.format_results(results, format="sarif")
        assert "$schema" in output or "sarif" in output.lower()
