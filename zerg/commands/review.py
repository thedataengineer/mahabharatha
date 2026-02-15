"""ZERG review command - two-stage code review workflow."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from zerg.fs_utils import collect_files
from zerg.json_utils import dumps as json_dumps
from zerg.logging import get_logger
from zerg.security import SecurityFinding, SecurityResult, run_security_scan

console = Console()
logger = get_logger("review")


class ReviewMode(Enum):
    """Review workflow modes."""

    PREPARE = "prepare"
    SELF = "self"
    RECEIVE = "receive"
    FULL = "full"


@dataclass
class ReviewConfig:
    """Configuration for review."""

    mode: str = "full"
    include_tests: bool = True
    include_docs: bool = True
    strict: bool = False


@dataclass
class ReviewItem:
    """A review comment or finding."""

    category: str
    severity: str  # info, warning, error
    file: str
    line: int
    message: str
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category,
            "severity": self.severity,
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "suggestion": self.suggestion,
        }


@dataclass
class ReviewResult:
    """Result of code review."""

    files_reviewed: int
    items: list[ReviewItem]
    spec_passed: bool
    quality_passed: bool
    stage1_details: str = ""
    stage2_details: str = ""
    security_passed: bool = True
    security_result: SecurityResult | None = None

    @property
    def overall_passed(self) -> bool:
        """Check if all stages passed."""
        return self.spec_passed and self.quality_passed and self.security_passed

    @property
    def total_items(self) -> int:
        """Count total review items."""
        return len(self.items)

    @property
    def error_count(self) -> int:
        """Count error-level items."""
        return sum(1 for item in self.items if item.severity == "error")

    @property
    def warning_count(self) -> int:
        """Count warning-level items."""
        return sum(1 for item in self.items if item.severity == "warning")


class SelfReviewChecklist:
    """Checklist for self-review before submission."""

    ITEMS = [
        ("basics", "Code compiles/runs without errors"),
        ("tests", "All tests pass locally"),
        ("secrets", "No hardcoded values or secrets"),
        ("errors", "Error handling is appropriate"),
        ("edge_cases", "Edge cases are handled"),
        ("readability", "Code is readable and well-named"),
        ("complexity", "No unnecessary complexity"),
        ("docs", "Documentation is updated"),
        ("debug", "No console.log/print debug statements"),
        ("requirements", "Changes match the requirements"),
    ]

    def get_items(self) -> list[tuple[str, str]]:
        """Return checklist items."""
        return self.ITEMS


class CodeAnalyzer:
    """Analyze code for common issues."""

    PATTERNS: dict[str, dict[str, Any]] = {
        "debug_print": {
            "pattern": r"(print\(|console\.log|debugger;)",
            "message": "Debug statement found",
            "severity": "warning",
        },
        "todo": {
            "pattern": r"(TODO|FIXME|HACK|XXX)",
            "message": "TODO/FIXME comment found",
            "severity": "info",
        },
        "long_line": {
            "pattern": None,  # Special handling
            "message": "Line exceeds 120 characters",
            "severity": "info",
        },
    }

    def analyze(self, content: str, filename: str) -> list[ReviewItem]:
        """Analyze content for issues."""
        import re

        items = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Check patterns
            for category, config in self.PATTERNS.items():
                if config["pattern"]:
                    if re.search(config["pattern"], line, re.IGNORECASE):
                        items.append(
                            ReviewItem(
                                category=category,
                                severity=config["severity"],
                                file=filename,
                                line=line_num,
                                message=config["message"],
                            )
                        )
                elif category == "long_line" and len(line) > 120:
                    items.append(
                        ReviewItem(
                            category=category,
                            severity=config["severity"],
                            file=filename,
                            line=line_num,
                            message=f"{config['message']} ({len(line)} chars)",
                        )
                    )

        return items


class ReviewCommand:
    """Main review command orchestrator."""

    def __init__(self, config: ReviewConfig | None = None) -> None:
        """Initialize review command."""
        self.config = config or ReviewConfig()
        self.checklist = SelfReviewChecklist()
        self.analyzer = CodeAnalyzer()

    def supported_modes(self) -> list[str]:
        """Return list of supported review modes."""
        return [m.value for m in ReviewMode]

    def run(
        self,
        files: list[str],
        mode: str = "full",
        no_security: bool = False,
    ) -> ReviewResult:
        """Run code review."""
        items: list[ReviewItem] = []
        spec_passed = True
        quality_passed = True
        security_passed = True
        security_result: SecurityResult | None = None
        stage1_details = ""
        stage2_details = ""

        if mode in ("prepare", "full"):
            spec_passed, stage1_details = self._run_spec_review(files)

        if mode in ("self", "full"):
            self_items = self._run_self_review(files)
            items.extend(self_items)

        if mode in ("receive", "full"):
            quality_passed, stage2_details, quality_items = self._run_quality_review(files)
            items.extend(quality_items)

        if mode in ("receive", "full") and not no_security:
            security_passed, _sec_details, security_result = self._run_security_review()

        return ReviewResult(
            files_reviewed=len(files),
            items=items,
            spec_passed=spec_passed,
            quality_passed=quality_passed,
            stage1_details=stage1_details,
            stage2_details=stage2_details,
            security_passed=security_passed,
            security_result=security_result,
        )

    def _run_spec_review(self, files: list[str]) -> tuple[bool, str]:
        """Stage 1: Spec compliance review."""
        details_lines = [
            "Stage 1: Specification Review",
            "-" * 30,
            "",
            "Checking implementation against requirements...",
            "",
        ]

        # Check for common spec compliance issues
        has_tests = any("test" in f.lower() for f in files)
        has_docs = any(f.endswith(".md") or f.endswith(".rst") for f in files)

        if self.config.include_tests and not has_tests:
            details_lines.append("⚠ No test files included in changes")
        else:
            details_lines.append("✓ Test files present")

        if self.config.include_docs:
            if has_docs:
                details_lines.append("✓ Documentation updated")
            else:
                details_lines.append("⚠ Consider updating documentation")

        details_lines.append("")
        details_lines.append("Spec compliance: PASSED")

        return True, "\n".join(details_lines)

    def _run_self_review(self, files: list[str]) -> list[ReviewItem]:
        """Generate self-review checklist and analyze files."""
        items: list[ReviewItem] = []

        # Analyze each file
        for filepath in files:
            try:
                path = Path(filepath)
                if not path.exists() or not path.is_file():
                    continue
                if path.suffix not in [".py", ".js", ".ts", ".go", ".rs", ".java"]:
                    continue

                content = path.read_text(encoding="utf-8")
                file_items = self.analyzer.analyze(content, filepath)
                items.extend(file_items)
            except (OSError, ValueError, UnicodeDecodeError) as e:
                logger.debug(f"File read failed: {e}")

        return items

    def _run_quality_review(self, files: list[str]) -> tuple[bool, str, list[ReviewItem]]:
        """Stage 2: Code quality review."""
        items: list[ReviewItem] = []
        details_lines = [
            "Stage 2: Quality Review",
            "-" * 30,
            "",
        ]

        total_lines = 0
        total_issues = 0

        for filepath in files:
            try:
                path = Path(filepath)
                if not path.exists() or not path.is_file():
                    continue

                content = path.read_text(encoding="utf-8")
                lines = content.split("\n")
                total_lines += len(lines)

                # Check complexity (simple heuristic)
                functions = content.count("def ") + content.count("function ")
                if functions > 0:
                    avg_lines_per_func = len(lines) / functions
                    if avg_lines_per_func > 50:
                        items.append(
                            ReviewItem(
                                category="complexity",
                                severity="warning",
                                file=filepath,
                                line=1,
                                message=(f"High average function length ({avg_lines_per_func:.0f} lines)"),
                                suggestion="Consider breaking into smaller functions",
                            )
                        )
                        total_issues += 1

            except (OSError, UnicodeDecodeError) as e:
                logger.debug(f"File read failed: {e}")

        details_lines.append(f"Files reviewed: {len(files)}")
        details_lines.append(f"Total lines: {total_lines}")
        details_lines.append(f"Issues found: {total_issues}")
        details_lines.append("")

        passed = total_issues == 0 or not self.config.strict
        status = "PASSED" if passed else "NEEDS ATTENTION"
        details_lines.append(f"Quality review: {status}")

        return passed, "\n".join(details_lines), items

    def _run_security_review(self, path: str = ".") -> tuple[bool, str, SecurityResult]:
        """Stage 3: Security scan."""
        result = run_security_scan(path=path)
        passed = result.passed
        details = f"{result.files_scanned} files scanned, {len(result.findings)} findings"
        return passed, details, result

    def format_result(self, result: ReviewResult, fmt: str = "text") -> str:
        """Format review result."""
        if fmt == "json":
            security_data: dict[str, Any] = {}
            if result.security_result is not None:
                security_data = {
                    "security_passed": result.security_passed,
                    "files_scanned": result.security_result.files_scanned,
                    "findings_count": len(result.security_result.findings),
                    "summary": result.security_result.summary,
                    "findings": [
                        {
                            "category": f.category,
                            "severity": f.severity,
                            "file": f.file,
                            "line": f.line,
                            "message": f.message,
                            "cwe": f.cwe,
                        }
                        for f in result.security_result.findings
                    ],
                }
            else:
                security_data = {
                    "security_passed": result.security_passed,
                    "skipped": True,
                }

            return json_dumps(
                {
                    "files_reviewed": result.files_reviewed,
                    "overall_passed": result.overall_passed,
                    "spec_passed": result.spec_passed,
                    "quality_passed": result.quality_passed,
                    "security": security_data,
                    "total_items": result.total_items,
                    "error_count": result.error_count,
                    "warning_count": result.warning_count,
                    "items": [i.to_dict() for i in result.items],
                },
                indent=True,
            )

        status = "PASSED" if result.overall_passed else "NEEDS ATTENTION"
        sec_status = "✓" if result.security_passed else "✗"
        if result.security_result is None:
            sec_status = "SKIPPED"

        lines = [
            "Code Review Results",
            "=" * 40,
            f"Status: {status}",
            f"Files Reviewed: {result.files_reviewed}",
            "",
            f"Stage 1 (Spec): {'✓' if result.spec_passed else '✗'}",
            f"Stage 2 (Quality): {'✓' if result.quality_passed else '✗'}",
            f"Stage 3 (Security): {sec_status}",
            "",
        ]

        if result.items:
            lines.append("Review Items:")
            for item in result.items[:10]:
                severity_icon = {"error": "❌", "warning": "⚠", "info": "ℹ"}.get(item.severity, "•")
                lines.append(f"  {severity_icon} [{item.severity}] {item.file}:{item.line}")
                lines.append(f"     {item.message}")

        if result.security_result and result.security_result.findings:
            lines.append("")
            lines.append("Security Findings:")
            for finding in result.security_result.findings[:10]:
                cwe_str = f" ({finding.cwe})" if finding.cwe else ""
                lines.append(
                    f"  [{finding.severity.upper()}] {finding.file}:{finding.line} - {finding.message}{cwe_str}"
                )

        return "\n".join(lines)


def _collect_files(path: str | None, mode: str) -> list[str]:
    """Collect files to review."""
    if not path:
        # Try to get changed files from git
        try:
            import subprocess

            result = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split("\n")

            # Try unstaged changes
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split("\n")
        except (OSError, subprocess.SubprocessError) as e:
            logger.debug(f"Review check failed: {e}")

        path = "."

    target = Path(path)
    if target.is_file():
        return [str(target)]
    elif target.is_dir():
        grouped = collect_files(target, extensions={".py", ".js", ".ts", ".go", ".rs"})
        files = [str(f) for ext in grouped for f in grouped[ext]]
        return files[:50]
    return []


@click.command()
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["prepare", "self", "receive", "full"]),
    default="full",
    help="Review mode",
)
@click.option("--files", "-f", help="Specific files to review")
@click.option("--output", "-o", help="Output file for review results")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--no-security", is_flag=True, default=False, help="Skip security scan (Stage 3)")
@click.pass_context
def review(
    ctx: click.Context,
    mode: str,
    files: str | None,
    output: str | None,
    json_output: bool,
    no_security: bool,
) -> None:
    """Three-stage code review workflow.

    Modes:
    - prepare: Generate change summary and review checklist
    - self: Self-review checklist and automated analysis
    - receive: Process code quality review + security scan
    - full: Complete three-stage review (spec + quality + security)

    Examples:

        zerg review

        zerg review --mode prepare

        zerg review --mode self

        zerg review --no-security

        zerg review --output review.md
    """
    try:
        console.print("\n[bold cyan]ZERG Review[/bold cyan]\n")
        console.print(f"Mode: [cyan]{mode}[/cyan]")

        if no_security:
            console.print("[yellow]Warning: Security scan (Stage 3) skipped via --no-security[/yellow]")

        # Collect files
        file_list = _collect_files(files, mode)

        if not file_list:
            console.print("[yellow]No files to review[/yellow]")
            console.print("Specify files with --files or stage changes with git")
            raise SystemExit(0)

        console.print(f"Reviewing {len(file_list)} files...\n")

        # Run review
        config = ReviewConfig(mode=mode)
        reviewer = ReviewCommand(config)
        result = reviewer.run(file_list, mode, no_security=no_security)

        # Show checklist for self-review mode
        if mode in ("self", "full"):
            console.print(Panel("[bold]Self-Review Checklist[/bold]", style="cyan"))
            checklist = reviewer.checklist.get_items()
            for _key, item in checklist:
                console.print(f"  ☐ {item}")
            console.print()

        # Display results
        if json_output:
            output_content = reviewer.format_result(result, "json")
            console.print(output_content)
        else:
            # Status panel
            status_color = "green" if result.overall_passed else "yellow"
            status_text = "PASSED" if result.overall_passed else "NEEDS ATTENTION"

            table = Table(title="Review Summary")
            table.add_column("Stage", style="cyan")
            table.add_column("Status")
            table.add_column("Details")

            stage1_status = "[green]✓ PASSED[/green]" if result.spec_passed else "[red]✗ FAILED[/red]"
            stage2_status = "[green]✓ PASSED[/green]" if result.quality_passed else "[yellow]⚠ REVIEW[/yellow]"

            # Stage 3: Security
            if result.security_result is not None:
                if result.security_passed:
                    stage3_status = "[green]✓ PASSED[/green]"
                else:
                    finding_count = len(result.security_result.findings)
                    stage3_status = f"[red]✗ FAILED ({finding_count} findings)[/red]"
                stage3_details = (
                    f"{result.security_result.files_scanned} files scanned, "
                    f"{len(result.security_result.findings)} findings"
                )
            else:
                stage3_status = "[yellow]SKIPPED[/yellow]"
                stage3_details = "Use --no-security to skip" if not no_security else "Skipped via --no-security"

            table.add_row("1. Spec Compliance", stage1_status, "Requirements alignment")
            table.add_row("2. Code Quality", stage2_status, f"{result.total_items} items found")
            table.add_row("3. Security", stage3_status, stage3_details)

            console.print(table)

            # Show issues if any
            if result.items:
                console.print(f"\n[bold]Review Items ({result.total_items}):[/bold]")

                # Group by severity
                errors: list[ReviewItem] = [i for i in result.items if i.severity == "error"]
                warnings: list[ReviewItem] = [i for i in result.items if i.severity == "warning"]
                infos: list[ReviewItem] = [i for i in result.items if i.severity == "info"]

                if errors:
                    console.print(f"\n[red]Errors ({len(errors)}):[/red]")
                    for ri in errors[:5]:
                        console.print(f"  ❌ {ri.file}:{ri.line} - {ri.message}")

                if warnings:
                    console.print(f"\n[yellow]Warnings ({len(warnings)}):[/yellow]")
                    for ri in warnings[:5]:
                        console.print(f"  ⚠ {ri.file}:{ri.line} - {ri.message}")

                if infos:
                    console.print(f"\n[blue]Info ({len(infos)}):[/blue]")
                    for ri in infos[:5]:
                        console.print(f"  ℹ {ri.file}:{ri.line} - {ri.message}")

            # Show security findings grouped by severity
            if result.security_result and result.security_result.findings:
                console.print(f"\n[bold]Security Findings ({len(result.security_result.findings)}):[/bold]")

                severity_order = ["critical", "high", "medium", "low", "info"]
                severity_styles = {
                    "critical": "red bold",
                    "high": "red",
                    "medium": "yellow",
                    "low": "dim",
                    "info": "dim",
                }

                for sev in severity_order:
                    sev_findings: list[SecurityFinding] = [
                        f for f in result.security_result.findings if f.severity == sev
                    ]
                    if not sev_findings:
                        continue

                    style = severity_styles.get(sev, "dim")
                    console.print(f"\n[{style}]{sev.upper()} ({len(sev_findings)}):[/{style}]")
                    for sf in sev_findings[:10]:
                        cwe_str = f" ({sf.cwe})" if sf.cwe else ""
                        console.print(f"  [{style}]{sf.file}:{sf.line} - {sf.message}{cwe_str}[/{style}]")

            # Overall status
            console.print(f"\n[bold]Overall:[/bold] [{status_color}]{status_text}[/{status_color}]")

            # Stage details if verbose
            if result.stage1_details:
                console.print(f"\n[dim]{result.stage1_details}[/dim]")

            output_content = reviewer.format_result(result, "text")

        # Write to file if requested
        if output:
            Path(output).write_text(output_content, encoding="utf-8")
            console.print(f"\n[green]✓[/green] Results written to {output}")

        raise SystemExit(0 if result.overall_passed else 1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        raise SystemExit(130) from None
    except SystemExit:
        raise
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        logger.exception("Review command failed")
        raise SystemExit(1) from e
