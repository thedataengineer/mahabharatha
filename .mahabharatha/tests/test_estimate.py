"""Tests for MAHABHARATHA v2 Estimate Command."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfidenceLevel:
    """Tests for ConfidenceLevel enum."""

    def test_levels_exist(self):
        """Test confidence levels are defined."""
        from estimate import ConfidenceLevel

        assert hasattr(ConfidenceLevel, "P50")
        assert hasattr(ConfidenceLevel, "P80")
        assert hasattr(ConfidenceLevel, "P95")


class TestEstimateConfig:
    """Tests for EstimateConfig dataclass."""

    def test_config_defaults(self):
        """Test EstimateConfig default values."""
        from estimate import EstimateConfig

        config = EstimateConfig()
        assert config.workers == 5
        assert config.confidence == 80
        assert config.include_cost is True

    def test_config_custom(self):
        """Test EstimateConfig with custom values."""
        from estimate import EstimateConfig

        config = EstimateConfig(workers=10, confidence=95)
        assert config.workers == 10
        assert config.confidence == 95


class TestTaskAnalysis:
    """Tests for TaskAnalysis dataclass."""

    def test_analysis_creation(self):
        """Test TaskAnalysis can be created."""
        from estimate import TaskAnalysis

        analysis = TaskAnalysis(total_tasks=20, levels=4, critical_path_length=6, max_parallelization=5)
        assert analysis.total_tasks == 20
        assert analysis.levels == 4

    def test_analysis_to_dict(self):
        """Test TaskAnalysis serialization."""
        from estimate import TaskAnalysis

        analysis = TaskAnalysis(total_tasks=10, levels=3, critical_path_length=3, max_parallelization=4)
        data = analysis.to_dict()
        assert data["total_tasks"] == 10
        assert data["levels"] == 3


class TestTimeEstimate:
    """Tests for TimeEstimate dataclass."""

    def test_estimate_creation(self):
        """Test TimeEstimate can be created."""
        from estimate import TimeEstimate

        est = TimeEstimate(confidence=80, duration_minutes=120, sessions=3)
        assert est.confidence == 80
        assert est.duration_minutes == 120

    def test_format_duration_hours(self):
        """Test formatting duration with hours."""
        from estimate import TimeEstimate

        est = TimeEstimate(confidence=80, duration_minutes=150, sessions=3)
        assert est.format_duration() == "2h 30m"

    def test_format_duration_minutes(self):
        """Test formatting duration without hours."""
        from estimate import TimeEstimate

        est = TimeEstimate(confidence=50, duration_minutes=45, sessions=1)
        assert est.format_duration() == "45m"


class TestResourceEstimate:
    """Tests for ResourceEstimate dataclass."""

    def test_resource_creation(self):
        """Test ResourceEstimate can be created."""
        from estimate import ResourceEstimate

        res = ResourceEstimate(optimal_workers=5, estimated_tokens=50000, api_cost=7.50)
        assert res.optimal_workers == 5
        assert res.api_cost == 7.50


class TestRiskFactor:
    """Tests for RiskFactor dataclass."""

    def test_risk_creation(self):
        """Test RiskFactor can be created."""
        from estimate import RiskFactor

        risk = RiskFactor(description="Complex integration", impact="medium")
        assert risk.description == "Complex integration"
        assert risk.impact == "medium"


class TestEstimateResult:
    """Tests for EstimateResult dataclass."""

    def test_result_creation(self):
        """Test EstimateResult can be created."""
        from estimate import EstimateResult, ResourceEstimate, TaskAnalysis

        analysis = TaskAnalysis(total_tasks=10, levels=3, critical_path_length=3, max_parallelization=4)
        resources = ResourceEstimate(optimal_workers=5, estimated_tokens=100000, api_cost=1.50)
        result = EstimateResult(
            feature="auth",
            task_analysis=analysis,
            time_estimates=[],
            resources=resources,
        )
        assert result.feature == "auth"

    def test_result_to_markdown(self):
        """Test EstimateResult markdown output."""
        from estimate import (
            EstimateResult,
            ResourceEstimate,
            TaskAnalysis,
            TimeEstimate,
        )

        analysis = TaskAnalysis(total_tasks=5, levels=2, critical_path_length=2, max_parallelization=3)
        resources = ResourceEstimate(optimal_workers=3, estimated_tokens=50000, api_cost=0.75)
        estimates = [TimeEstimate(confidence=80, duration_minutes=60, sessions=1)]
        result = EstimateResult(
            feature="test",
            task_analysis=analysis,
            time_estimates=estimates,
            resources=resources,
        )
        md = result.to_markdown()
        assert "# Estimation: test" in md
        assert "Task Analysis" in md


class TestTaskGraphAnalyzer:
    """Tests for TaskGraphAnalyzer."""

    def test_analyzer_creation(self):
        """Test TaskGraphAnalyzer can be created."""
        from estimate import TaskGraphAnalyzer

        analyzer = TaskGraphAnalyzer()
        assert analyzer is not None

    def test_analyze_nonexistent_file(self):
        """Test analyzing non-existent file."""
        from estimate import TaskGraphAnalyzer

        analyzer = TaskGraphAnalyzer()
        result = analyzer.analyze(Path("/nonexistent/graph.json"))
        assert result.total_tasks == 0


class TestTimeEstimator:
    """Tests for TimeEstimator."""

    def test_estimator_creation(self):
        """Test TimeEstimator can be created."""
        from estimate import TimeEstimator

        estimator = TimeEstimator()
        assert estimator is not None

    def test_estimate_returns_multiple_confidences(self):
        """Test estimate returns multiple confidence levels."""
        from estimate import TaskAnalysis, TimeEstimator

        estimator = TimeEstimator()
        analysis = TaskAnalysis(total_tasks=10, levels=3, critical_path_length=3, max_parallelization=5)
        estimates = estimator.estimate(analysis, workers=5)
        assert len(estimates) == 3
        confidences = [e.confidence for e in estimates]
        assert 50 in confidences
        assert 80 in confidences
        assert 95 in confidences


class TestEstimateCommand:
    """Tests for EstimateCommand."""

    def test_command_creation(self):
        """Test EstimateCommand can be created."""
        from estimate import EstimateCommand

        cmd = EstimateCommand()
        assert cmd is not None

    def test_command_run(self):
        """Test running estimation."""
        from estimate import EstimateCommand, EstimateResult

        cmd = EstimateCommand()
        result = cmd.run(feature="test-feature", workers=5)
        assert isinstance(result, EstimateResult)
        assert result.feature == "test-feature"

    def test_command_format_json(self):
        """Test JSON output formatting."""
        import json

        from estimate import (
            EstimateCommand,
            EstimateResult,
            ResourceEstimate,
            TaskAnalysis,
        )

        cmd = EstimateCommand()
        analysis = TaskAnalysis(total_tasks=5, levels=2, critical_path_length=2, max_parallelization=3)
        resources = ResourceEstimate(optimal_workers=3, estimated_tokens=50000, api_cost=0.75)
        result = EstimateResult(
            feature="test",
            task_analysis=analysis,
            time_estimates=[],
            resources=resources,
        )
        output = cmd.format_result(result, format="json")
        data = json.loads(output)
        assert data["feature"] == "test"
