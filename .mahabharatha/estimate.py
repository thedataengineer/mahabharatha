"""MAHABHARATHA v2 Estimate Command - Development estimation with confidence intervals."""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ConfidenceLevel(Enum):
    """Confidence interval levels."""

    P50 = 50  # 50% confidence
    P80 = 80  # 80% confidence
    P95 = 95  # 95% confidence


@dataclass
class EstimateConfig:
    """Configuration for estimation."""

    workers: int = 5
    confidence: int = 80
    include_cost: bool = True
    token_rate: float = 0.015  # $ per 1K tokens


@dataclass
class TaskAnalysis:
    """Analysis of task graph."""

    total_tasks: int
    levels: int
    critical_path_length: int
    max_parallelization: int
    complex_tasks: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_tasks": self.total_tasks,
            "levels": self.levels,
            "critical_path_length": self.critical_path_length,
            "max_parallelization": self.max_parallelization,
            "complex_tasks": self.complex_tasks,
        }


@dataclass
class TimeEstimate:
    """Time estimate with confidence."""

    confidence: int
    duration_minutes: int
    sessions: int

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "confidence": self.confidence,
            "duration_minutes": self.duration_minutes,
            "sessions": self.sessions,
        }

    def format_duration(self) -> str:
        """Format duration as human readable."""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


@dataclass
class ResourceEstimate:
    """Resource requirements estimate."""

    optimal_workers: int
    estimated_tokens: int
    api_cost: float

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "optimal_workers": self.optimal_workers,
            "estimated_tokens": self.estimated_tokens,
            "api_cost": round(self.api_cost, 2),
        }


@dataclass
class RiskFactor:
    """A risk factor affecting the estimate."""

    description: str
    impact: str  # low, medium, high
    mitigation: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "description": self.description,
            "impact": self.impact,
            "mitigation": self.mitigation,
        }


@dataclass
class EstimateResult:
    """Complete estimation result."""

    feature: str
    task_analysis: TaskAnalysis
    time_estimates: list[TimeEstimate]
    resources: ResourceEstimate
    risks: list[RiskFactor] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "feature": self.feature,
            "task_analysis": self.task_analysis.to_dict(),
            "time_estimates": [t.to_dict() for t in self.time_estimates],
            "resources": self.resources.to_dict(),
            "risks": [r.to_dict() for r in self.risks],
        }

    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            f"# Estimation: {self.feature}",
            "",
            "## Task Analysis",
            f"- Total tasks: {self.task_analysis.total_tasks}",
            f"- Levels: {self.task_analysis.levels}",
            f"- Critical path: {self.task_analysis.critical_path_length} tasks",
            f"- Max parallelization: {self.task_analysis.max_parallelization} tasks",
            "",
            "## Time Estimates",
            "",
            "| Confidence | Duration | Sessions |",
            "|------------|----------|----------|",
        ]

        for est in self.time_estimates:
            lines.append(f"| {est.confidence}% | {est.format_duration()} | {est.sessions} |")

        lines.extend(
            [
                "",
                "## Resource Requirements",
                f"- Optimal workers: {self.resources.optimal_workers}",
                f"- Estimated tokens: {self.resources.estimated_tokens:,}",
                f"- API cost: ~${self.resources.api_cost:.2f}",
            ]
        )

        if self.risks:
            lines.extend(["", "## Risks"])
            for risk in self.risks:
                lines.append(f"- **{risk.impact.upper()}**: {risk.description}")

        return "\n".join(lines)


class TaskGraphAnalyzer:
    """Analyze task graphs for estimation."""

    def analyze(self, graph_path: Path) -> TaskAnalysis:
        """Analyze a task graph file."""
        try:
            with open(graph_path) as f:
                data = json.load(f)

            tasks = data.get("tasks", [])
            levels = data.get("levels", {})

            # Calculate metrics
            total = len(tasks)
            level_count = len(levels)
            critical_path = len(data.get("critical_path", []))
            max_parallel = data.get("max_parallelization", 1)

            # Count complex tasks
            complex_count = sum(1 for t in tasks if t.get("estimate_minutes", 0) > 30)

            return TaskAnalysis(
                total_tasks=total,
                levels=level_count,
                critical_path_length=critical_path,
                max_parallelization=max_parallel,
                complex_tasks=complex_count,
            )
        except (OSError, json.JSONDecodeError):
            return TaskAnalysis(
                total_tasks=0,
                levels=0,
                critical_path_length=0,
                max_parallelization=0,
            )

    def analyze_from_data(self, tasks: list[dict], levels: int) -> TaskAnalysis:
        """Analyze from task data directly."""
        return TaskAnalysis(
            total_tasks=len(tasks),
            levels=levels,
            critical_path_length=levels,  # Simplified
            max_parallelization=max(1, len(tasks) // levels) if levels > 0 else 1,
        )


class TimeEstimator:
    """Estimate time with confidence intervals."""

    # Multipliers for confidence levels
    CONFIDENCE_MULTIPLIERS = {
        50: 1.0,
        80: 1.7,
        95: 2.7,
    }

    def estimate(self, analysis: TaskAnalysis, workers: int = 5) -> list[TimeEstimate]:
        """Generate time estimates at multiple confidence levels."""
        # Base estimate: assume 20 min per task
        base_minutes = analysis.total_tasks * 20

        # Adjust for parallelization
        parallel_factor = min(workers, analysis.max_parallelization)
        adjusted = base_minutes / parallel_factor if parallel_factor > 0 else base_minutes

        estimates = []
        for confidence, multiplier in self.CONFIDENCE_MULTIPLIERS.items():
            duration = int(adjusted * multiplier)
            sessions = max(1, duration // 60)  # ~1 hour per session
            estimates.append(
                TimeEstimate(
                    confidence=confidence,
                    duration_minutes=duration,
                    sessions=sessions,
                )
            )

        return estimates


class ResourceEstimator:
    """Estimate resource requirements."""

    def estimate(
        self,
        analysis: TaskAnalysis,
        config: EstimateConfig,
    ) -> ResourceEstimate:
        """Estimate resources needed."""
        # Estimate tokens: ~20K per task
        tokens = analysis.total_tasks * 20000

        # Calculate cost
        cost = (tokens / 1000) * config.token_rate

        # Optimal workers based on max parallelization
        optimal = min(config.workers, analysis.max_parallelization)

        return ResourceEstimate(
            optimal_workers=optimal,
            estimated_tokens=tokens,
            api_cost=cost,
        )


class RiskAnalyzer:
    """Analyze risks affecting estimates."""

    def analyze(self, analysis: TaskAnalysis) -> list[RiskFactor]:
        """Identify risks from task analysis."""
        risks = []

        if analysis.complex_tasks > 0:
            risks.append(
                RiskFactor(
                    description=f"Level contains {analysis.complex_tasks} complex tasks",
                    impact="medium",
                    mitigation="Consider breaking into smaller tasks",
                )
            )

        if analysis.critical_path_length > 5:
            risks.append(
                RiskFactor(
                    description="Long critical path may cause delays",
                    impact="medium",
                    mitigation="Identify parallelization opportunities",
                )
            )

        if analysis.max_parallelization < 3:
            risks.append(
                RiskFactor(
                    description="Limited parallelization potential",
                    impact="low",
                    mitigation="Ensure worker count matches parallelization",
                )
            )

        return risks


class EstimateCommand:
    """Main estimate command orchestrator."""

    def __init__(self, config: EstimateConfig | None = None):
        """Initialize estimate command."""
        self.config = config or EstimateConfig()
        self.graph_analyzer = TaskGraphAnalyzer()
        self.time_estimator = TimeEstimator()
        self.resource_estimator = ResourceEstimator()
        self.risk_analyzer = RiskAnalyzer()

    def run(
        self,
        graph_path: str = "",
        feature: str = "feature",
        workers: int = 5,
    ) -> EstimateResult:
        """Run estimation."""
        # Analyze task graph
        if graph_path:
            analysis = self.graph_analyzer.analyze(Path(graph_path))
        else:
            # Default analysis for no graph
            analysis = TaskAnalysis(
                total_tasks=10,
                levels=3,
                critical_path_length=3,
                max_parallelization=5,
            )

        # Generate estimates
        self.config.workers = workers
        time_estimates = self.time_estimator.estimate(analysis, workers)
        resources = self.resource_estimator.estimate(analysis, self.config)
        risks = self.risk_analyzer.analyze(analysis)

        return EstimateResult(
            feature=feature,
            task_analysis=analysis,
            time_estimates=time_estimates,
            resources=resources,
            risks=risks,
        )

    def format_result(self, result: EstimateResult, format: str = "text") -> str:
        """Format estimation result."""
        if format == "json":
            return json.dumps(result.to_dict(), indent=2)

        if format == "markdown":
            return result.to_markdown()

        lines = [
            "Estimation Result",
            "=" * 40,
            f"Feature: {result.feature}",
            "",
            "Task Analysis:",
            f"  Tasks: {result.task_analysis.total_tasks}",
            f"  Levels: {result.task_analysis.levels}",
            "",
            "Time Estimates:",
        ]

        for est in result.time_estimates:
            lines.append(f"  {est.confidence}%: {est.format_duration()} ({est.sessions} sessions)")

        lines.extend(
            [
                "",
                "Resources:",
                f"  Workers: {result.resources.optimal_workers}",
                f"  Tokens: {result.resources.estimated_tokens:,}",
                f"  Cost: ${result.resources.api_cost:.2f}",
            ]
        )

        return "\n".join(lines)


__all__ = [
    "ConfidenceLevel",
    "EstimateConfig",
    "TaskAnalysis",
    "TimeEstimate",
    "ResourceEstimate",
    "RiskFactor",
    "EstimateResult",
    "TaskGraphAnalyzer",
    "TimeEstimator",
    "ResourceEstimator",
    "RiskAnalyzer",
    "EstimateCommand",
]
