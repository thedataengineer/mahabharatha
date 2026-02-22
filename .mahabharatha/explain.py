"""MAHABHARATHA v2 Explain Command - Code and concept explanation with audience targeting."""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Audience(Enum):
    """Target audience levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class ExplainDepth(Enum):
    """Explanation depth levels."""

    SUMMARY = "summary"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


@dataclass
class ExplainConfig:
    """Configuration for explanations."""

    audience: str = "intermediate"
    depth: str = "detailed"
    include_callers: bool = False
    include_callees: bool = False
    include_examples: bool = True
    include_diagram: bool = True


@dataclass
class CodeReference:
    """A reference to code location."""

    file: str
    line: int
    name: str
    ref_type: str  # caller, callee, definition

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "file": self.file,
            "line": self.line,
            "name": self.name,
            "ref_type": self.ref_type,
        }


@dataclass
class ExplainResult:
    """Result of explanation generation."""

    target: str
    summary: str
    explanation: str
    audience: str
    depth: str
    references: list[CodeReference] = field(default_factory=list)
    diagram: str = ""
    security_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "target": self.target,
            "summary": self.summary,
            "explanation": self.explanation,
            "audience": self.audience,
            "depth": self.depth,
            "references": [r.to_dict() for r in self.references],
            "diagram": self.diagram,
            "security_notes": self.security_notes,
        }

    def to_markdown(self) -> str:
        """Generate markdown output."""
        lines = [
            f"# {self.target}",
            "",
            "## Summary",
            self.summary,
            "",
            "## Explanation",
            self.explanation,
        ]

        if self.diagram:
            lines.extend(["", "## Data Flow", self.diagram])

        if self.references:
            lines.extend(["", "## References"])
            for ref in self.references:
                lines.append(f"- `{ref.file}:{ref.line}` - {ref.name} ({ref.ref_type})")

        if self.security_notes:
            lines.extend(["", "## Security Considerations"])
            for note in self.security_notes:
                lines.append(f"- {note}")

        return "\n".join(lines)


class CodeAnalyzer:
    """Analyze code for explanation."""

    def analyze_file(self, filepath: Path) -> dict:
        """Analyze a source file."""
        try:
            content = filepath.read_text()
            lines = content.split("\n")
            return {
                "path": str(filepath),
                "lines": len(lines),
                "language": self._detect_language(filepath),
                "has_docstring": '"""' in content or "'''" in content,
            }
        except OSError:
            return {"path": str(filepath), "error": "Could not read file"}

    def analyze_function(self, filepath: Path, function_name: str) -> dict:
        """Analyze a specific function."""
        try:
            content = filepath.read_text()
            # Simple pattern matching for function definition
            if f"def {function_name}" in content or f"function {function_name}" in content:
                return {
                    "name": function_name,
                    "found": True,
                    "file": str(filepath),
                }
            return {"name": function_name, "found": False}
        except OSError:
            return {"name": function_name, "error": "Could not read file"}

    def _detect_language(self, filepath: Path) -> str:
        """Detect language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".rs": "rust",
            ".go": "go",
        }
        return ext_map.get(filepath.suffix.lower(), "unknown")


class ExplanationGenerator:
    """Generate explanations for code."""

    def __init__(self, config: ExplainConfig | None = None):
        """Initialize generator."""
        self.config = config or ExplainConfig()
        self.analyzer = CodeAnalyzer()

    def explain_file(self, filepath: Path) -> ExplainResult:
        """Generate explanation for a file."""
        analysis = self.analyzer.analyze_file(filepath)

        if "error" in analysis:
            return ExplainResult(
                target=str(filepath),
                summary=f"Could not analyze: {analysis['error']}",
                explanation="",
                audience=self.config.audience,
                depth=self.config.depth,
            )

        summary = f"A {analysis['language']} file with {analysis['lines']} lines."
        explanation = self._generate_explanation(analysis)

        diagram = ""
        if self.config.include_diagram:
            diagram = self._generate_diagram(filepath)

        return ExplainResult(
            target=str(filepath),
            summary=summary,
            explanation=explanation,
            audience=self.config.audience,
            depth=self.config.depth,
            diagram=diagram,
        )

    def explain_function(self, filepath: Path, function_name: str) -> ExplainResult:
        """Generate explanation for a function."""
        analysis = self.analyzer.analyze_function(filepath, function_name)

        if not analysis.get("found"):
            return ExplainResult(
                target=f"{filepath}:{function_name}",
                summary=f"Function {function_name} not found",
                explanation="",
                audience=self.config.audience,
                depth=self.config.depth,
            )

        return ExplainResult(
            target=f"{filepath}:{function_name}",
            summary=f"Function {function_name} in {filepath}",
            explanation=f"Detailed analysis of {function_name}.",
            audience=self.config.audience,
            depth=self.config.depth,
        )

    def explain_concept(self, concept: str) -> ExplainResult:
        """Generate explanation for a concept."""
        # Adapt explanation to audience level
        if self.config.audience == "beginner":
            explanation = f"A simple introduction to {concept}."
        elif self.config.audience == "expert":
            explanation = f"Advanced technical details of {concept}."
        else:
            explanation = f"A comprehensive overview of {concept}."

        return ExplainResult(
            target=concept,
            summary=f"Concept: {concept}",
            explanation=explanation,
            audience=self.config.audience,
            depth=self.config.depth,
        )

    def _generate_explanation(self, analysis: dict) -> str:
        """Generate explanation text based on analysis."""
        lang = analysis.get("language", "unknown")
        lines = analysis.get("lines", 0)

        if self.config.depth == "summary":
            return f"A {lang} source file."
        elif self.config.depth == "comprehensive":
            return f"A {lang} source file containing {lines} lines of code. " + (
                "Includes documentation." if analysis.get("has_docstring") else ""
            )
        else:
            return f"A {lang} source file with {lines} lines."

    def _generate_diagram(self, filepath: Path) -> str:
        """Generate mermaid diagram."""
        return f"""```mermaid
flowchart LR
    A[Input] --> B[{filepath.stem}]
    B --> C[Output]
```"""


class ExplainCommand:
    """Main explain command orchestrator."""

    def __init__(self, config: ExplainConfig | None = None):
        """Initialize explain command."""
        self.config = config or ExplainConfig()
        self.generator = ExplanationGenerator(config=self.config)

    def run(
        self,
        target: str,
        target_type: str = "file",
        function_name: str = "",
    ) -> ExplainResult:
        """Run explanation generation."""
        if target_type == "concept":
            return self.generator.explain_concept(target)

        filepath = Path(target)

        if target_type == "function" and function_name:
            return self.generator.explain_function(filepath, function_name)

        return self.generator.explain_file(filepath)

    def format_result(self, result: ExplainResult, format: str = "text") -> str:
        """Format explanation result."""
        if format == "json":
            return json.dumps(result.to_dict(), indent=2)

        if format == "markdown":
            return result.to_markdown()

        lines = [
            "Explanation",
            "=" * 40,
            f"Target: {result.target}",
            f"Audience: {result.audience}",
            f"Depth: {result.depth}",
            "",
            "Summary:",
            result.summary,
            "",
            "Explanation:",
            result.explanation,
        ]

        return "\n".join(lines)


__all__ = [
    "Audience",
    "ExplainDepth",
    "ExplainConfig",
    "CodeReference",
    "ExplainResult",
    "CodeAnalyzer",
    "ExplanationGenerator",
    "ExplainCommand",
]
