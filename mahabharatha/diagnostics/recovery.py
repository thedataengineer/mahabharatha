"""Recovery planning and execution for MAHABHARATHA debugging."""

from __future__ import annotations

import shlex
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from mahabharatha.command_executor import CommandValidationError, get_executor
from mahabharatha.logging import get_logger

if TYPE_CHECKING:
    from mahabharatha.commands.debug import DiagnosticResult
    from mahabharatha.diagnostics.state_introspector import MahabharathaHealthReport

logger = get_logger("diagnostics.recovery")

SUBPROCESS_TIMEOUT = 10

# Keywords in fix text that suggest architectural changes are needed
ARCHITECTURAL_KEYWORDS = frozenset(
    {
        "refactor",
        "redesign",
        "new component",
        "restructure",
        "rearchitect",
        "split module",
        "extract service",
        "new abstraction",
        "rewrite",
    }
)

# Default threshold for multi-task failure escalation (configurable)
DESIGN_ESCALATION_TASK_THRESHOLD = 3


@dataclass
class RecoveryStep:
    """A single recovery action."""

    description: str
    command: str
    risk: str = "safe"  # "safe" | "moderate" | "destructive"
    reversible: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "description": self.description,
            "command": self.command,
            "risk": self.risk,
            "reversible": self.reversible,
        }


@dataclass
class RecoveryPlan:
    """A complete recovery plan with steps."""

    problem: str
    root_cause: str
    steps: list[RecoveryStep] = field(default_factory=list)
    verification_command: str = ""
    prevention: str = ""
    needs_design: bool = False
    design_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "problem": self.problem,
            "root_cause": self.root_cause,
            "steps": [s.to_dict() for s in self.steps],
            "verification_command": self.verification_command,
            "prevention": self.prevention,
            "needs_design": self.needs_design,
            "design_reason": self.design_reason,
        }


# Template recovery steps by error category
RECOVERY_TEMPLATES: dict[str, list[RecoveryStep]] = {
    "worker_crash": [
        RecoveryStep(
            description="Clean up stale worktrees",
            command="git worktree prune",
            risk="safe",
            reversible=True,
        ),
        RecoveryStep(
            description="Reset failed task states to pending",
            command="mahabharatha debug --auto-fix",
            risk="moderate",
            reversible=True,
        ),
        RecoveryStep(
            description="Restart the kurukshetra",
            command="mahabharatha kurukshetra --resume",
            risk="safe",
            reversible=True,
        ),
    ],
    "state_corruption": [
        RecoveryStep(
            description="Restore state from backup",
            command="cp .mahabharatha/state/{feature}.json.bak .mahabharatha/state/{feature}.json",
            risk="moderate",
            reversible=True,
        ),
        RecoveryStep(
            description="Validate restored state",
            command="python -c \"import json; json.load(open('.mahabharatha/state/{feature}.json'))\"",
            risk="safe",
            reversible=True,
        ),
    ],
    "git_conflict": [
        RecoveryStep(
            description="Abort any in-progress merge",
            command="git merge --abort",
            risk="moderate",
            reversible=True,
        ),
        RecoveryStep(
            description="Prune worktrees",
            command="git worktree prune",
            risk="safe",
            reversible=True,
        ),
    ],
    "port_conflict": [
        RecoveryStep(
            description="List processes on conflicting ports",
            command="lsof -i :{port}",
            risk="safe",
            reversible=True,
        ),
    ],
    "disk_space": [
        RecoveryStep(
            description="Clean up worktrees",
            command="git worktree prune && rm -rf .mahabharatha/worktrees/*/",
            risk="moderate",
            reversible=False,
        ),
        RecoveryStep(
            description="Clean docker artifacts",
            command="docker system prune -f",
            risk="moderate",
            reversible=False,
        ),
    ],
    "import_error": [
        RecoveryStep(
            description="Install missing dependencies",
            command="pip install -e .",
            risk="safe",
            reversible=True,
        ),
    ],
    "task_failure": [
        RecoveryStep(
            description="Review failed task logs",
            command="mahabharatha logs --worker {worker_id}",
            risk="safe",
            reversible=True,
        ),
        RecoveryStep(
            description="Retry failed tasks",
            command="mahabharatha retry --feature {feature}",
            risk="safe",
            reversible=True,
        ),
    ],
}


class RecoveryPlanner:
    """Generate and execute recovery plans from diagnostic results."""

    def __init__(self) -> None:
        """Initialize the recovery planner with a secure command executor."""
        self._executor = get_executor(allow_unlisted=True, timeout=SUBPROCESS_TIMEOUT)

    def plan(
        self,
        result: DiagnosticResult,
        health: MahabharathaHealthReport | None = None,
    ) -> RecoveryPlan:
        """Generate a recovery plan from diagnostic result and health report."""
        category = self._classify_error(result, health)
        steps = self._get_steps(category, result, health)

        feature = ""
        if health:
            feature = health.feature

        plan = RecoveryPlan(
            problem=result.symptom,
            root_cause=result.root_cause,
            steps=steps,
            verification_command=self._get_verification(category, feature),
            prevention=self._get_prevention(category),
        )

        needs, reason = self._check_design_escalation(category, result, health)
        plan.needs_design = needs
        plan.design_reason = reason

        return plan

    def _classify_error(
        self,
        result: DiagnosticResult,
        health: MahabharathaHealthReport | None,
    ) -> str:
        """Classify the error into a recovery category."""
        symptom_lower = result.symptom.lower()
        root_lower = result.root_cause.lower()
        combined = f"{symptom_lower} {root_lower}"

        if health and health.global_error:
            combined += f" {health.global_error.lower()}"

        if "corrupt" in combined or "json" in combined:
            return "state_corruption"
        if "worker" in combined and ("crash" in combined or "fail" in combined):
            return "worker_crash"
        if "port" in combined and "conflict" in combined:
            return "port_conflict"
        if "address already in use" in combined:
            return "port_conflict"
        if "merge" in combined or "git conflict" in combined:
            return "git_conflict"
        if "conflict" in combined:
            return "git_conflict"
        if "disk" in combined or "no space" in combined:
            return "disk_space"
        if "importerror" in combined or "modulenotfounderror" in combined:
            return "import_error"
        if "missing module" in combined or "no module" in combined:
            return "import_error"
        if health and health.failed_tasks:
            return "task_failure"
        return "task_failure"

    def _get_steps(
        self,
        category: str,
        result: DiagnosticResult,
        health: MahabharathaHealthReport | None,
    ) -> list[RecoveryStep]:
        """Get recovery steps for a category, with variable substitution."""
        template = RECOVERY_TEMPLATES.get(category, RECOVERY_TEMPLATES["task_failure"])
        steps: list[RecoveryStep] = []

        feature = health.feature if health else "unknown"
        worker_id = ""
        if health and health.failed_tasks:
            wid = health.failed_tasks[0].get("worker_id")
            worker_id = str(wid) if wid is not None else ""

        for tmpl in template:
            cmd = tmpl.command.format(
                feature=shlex.quote(feature),
                worker_id=shlex.quote(worker_id) if worker_id else "",
                port="",
            )
            steps.append(
                RecoveryStep(
                    description=tmpl.description,
                    command=cmd,
                    risk=tmpl.risk,
                    reversible=tmpl.reversible,
                )
            )

        return steps

    def _get_verification(self, category: str, feature: str) -> str:
        """Get verification command for a category."""
        verifications = {
            "state_corruption": (f"python -c \"import json; json.load(open('.mahabharatha/state/{feature}.json'))\""),
            "worker_crash": "mahabharatha status",
            "git_conflict": "git status",
            "port_conflict": "mahabharatha status --ports",
            "disk_space": "df -h .",
            "import_error": "python -c 'import mahabharatha'",
            "task_failure": "mahabharatha status",
        }
        return verifications.get(category, "mahabharatha status")

    def _get_prevention(self, category: str) -> str:
        """Get prevention advice for a category."""
        preventions = {
            "state_corruption": "Enable state file backups and validate JSON after writes",
            "worker_crash": "Monitor worker health, set appropriate timeouts",
            "git_conflict": "Ensure strict file ownership in task graph",
            "port_conflict": "Use unique port ranges per feature",
            "disk_space": "Clean up worktrees after each run",
            "import_error": "Pin dependencies and use virtual environments",
            "task_failure": "Add retry logic and improve verification commands",
        }
        return preventions.get(category, "Review logs and improve error handling")

    def _check_design_escalation(
        self,
        category: str,
        result: DiagnosticResult,
        health: MahabharathaHealthReport | None,
        threshold: int = DESIGN_ESCALATION_TASK_THRESHOLD,
    ) -> tuple[bool, str]:
        """Check if diagnosed issues need architectural redesign via /mahabharatha:design.

        Returns (needs_design, reason) tuple.
        """
        # Heuristic 1: 3+ tasks failed at same level → task graph design flaw
        if health and health.failed_tasks:
            failed_levels: dict[int, int] = {}
            for task in health.failed_tasks:
                level = task.get("level", 0)
                failed_levels[level] = failed_levels.get(level, 0) + 1
            for level, count in failed_levels.items():
                if count >= threshold:
                    return (
                        True,
                        f"{count} tasks failed at level {level} — task graph may have a design flaw",
                    )

        # Heuristic 2: git_conflict category with health data → file ownership
        if category == "git_conflict" and health is not None:
            return (
                True,
                "Git conflicts with active health data — file ownership needs redesign",
            )

        # Heuristic 3: Fix text contains architectural keywords
        combined_text = f"{result.root_cause} {result.recommendation}".lower()
        for keyword in ARCHITECTURAL_KEYWORDS:
            if keyword in combined_text:
                return (
                    True,
                    f"Root cause/recommendation mentions '{keyword}' — architectural change needed",
                )

        # Heuristic 4: Fix spans 3+ distinct files → wide blast radius
        if health and health.failed_tasks:
            files: set[str] = set()
            for task in health.failed_tasks:
                for f in task.get("owned_files", []):
                    files.add(f)
            if len(files) >= 3:
                return (
                    True,
                    f"Failures span {len(files)} files — wide blast radius needs coordinated design",
                )

        return False, ""

    def execute_step(
        self,
        step: RecoveryStep,
        confirm_fn: Callable[[RecoveryStep], bool] | None = None,
    ) -> dict[str, Any]:
        """Execute a recovery step with optional confirmation."""
        if confirm_fn and not confirm_fn(step):
            return {"success": False, "output": "Skipped by user", "skipped": True}

        try:
            result = self._executor.execute(
                step.command,
                timeout=SUBPROCESS_TIMEOUT,
            )
            return {
                "success": result.success,
                "output": result.stdout or result.stderr,
                "skipped": False,
            }
        except CommandValidationError as e:
            return {"success": False, "output": f"Command validation failed: {e}", "skipped": False}
        except OSError as e:
            return {"success": False, "output": str(e), "skipped": False}
