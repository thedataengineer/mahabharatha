"""ZERG v2 Document Command - Documentation generation and maintenance."""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class DocType(Enum):
    """Documentation types."""

    API = "api"
    README = "readme"
    ARCHITECTURE = "architecture"
    CHANGELOG = "changelog"


@dataclass
class DocConfig:
    """Configuration for documentation."""

    doc_type: str = "api"
    output: str = ""
    update: bool = False
    diagram: bool = False


@dataclass
class DocSection:
    """A documentation section."""

    title: str
    content: str
    level: int = 1

    def to_markdown(self) -> str:
        """Convert to markdown."""
        prefix = "#" * self.level
        return f"{prefix} {self.title}\n\n{self.content}"


@dataclass
class DocResult:
    """Result of documentation generation."""

    doc_type: str
    sections: list[DocSection]
    output_path: str = ""
    generated_at: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "doc_type": self.doc_type,
            "sections": [{"title": s.title, "level": s.level} for s in self.sections],
            "output_path": self.output_path,
            "generated_at": self.generated_at,
        }

    def to_markdown(self) -> str:
        """Generate full markdown document."""
        return "\n\n".join(s.to_markdown() for s in self.sections)


class APIDocGenerator:
    """Generate API documentation from code."""

    def generate(self, files: list[Path]) -> list[DocSection]:
        """Generate API docs from source files."""
        sections = [
            DocSection(
                title="API Reference",
                content="Auto-generated API documentation.",
                level=1,
            )
        ]

        for filepath in files:
            if filepath.suffix == ".py":
                sections.append(self._parse_python(filepath))

        return sections

    def _parse_python(self, filepath: Path) -> DocSection:
        """Parse Python file for documentation."""
        try:
            filepath.read_text()  # Verify file is readable
            doc = f"Module: `{filepath.name}`"
        except OSError:
            doc = f"Could not read {filepath}"

        return DocSection(title=filepath.stem, content=doc, level=2)


class ReadmeGenerator:
    """Generate README documentation."""

    def generate(self, project_path: Path) -> list[DocSection]:
        """Generate README sections."""
        sections = [
            DocSection(
                title="Project Name",
                content="Description of the project.",
                level=1,
            ),
            DocSection(
                title="Installation",
                content="```bash\npip install .\n```",
                level=2,
            ),
            DocSection(
                title="Usage",
                content="Basic usage instructions.",
                level=2,
            ),
            DocSection(
                title="License",
                content="MIT",
                level=2,
            ),
        ]
        return sections


class ArchitectureGenerator:
    """Generate architecture documentation."""

    def generate(self, project_path: Path, diagram: bool = False) -> list[DocSection]:
        """Generate architecture docs."""
        sections = [
            DocSection(
                title="System Architecture",
                content="Overview of the system architecture.",
                level=1,
            ),
            DocSection(
                title="Components",
                content="Description of main components.",
                level=2,
            ),
        ]

        if diagram:
            mermaid = """```mermaid
graph TD
    A[Client] --> B[API]
    B --> C[Service]
    C --> D[Database]
```"""
            sections.append(
                DocSection(title="Architecture Diagram", content=mermaid, level=2)
            )

        return sections


class DocumentCommand:
    """Main document command orchestrator."""

    def __init__(self, config: DocConfig | None = None):
        """Initialize document command."""
        self.config = config or DocConfig()
        self.api_gen = APIDocGenerator()
        self.readme_gen = ReadmeGenerator()
        self.arch_gen = ArchitectureGenerator()

    def run(
        self,
        doc_type: str = "api",
        path: str = ".",
        dry_run: bool = False,
    ) -> DocResult:
        """Generate documentation."""
        project_path = Path(path)

        if doc_type == "api":
            files = list(project_path.glob("**/*.py"))[:10]
            sections = self.api_gen.generate(files)
        elif doc_type == "readme":
            sections = self.readme_gen.generate(project_path)
        elif doc_type == "architecture":
            sections = self.arch_gen.generate(project_path, self.config.diagram)
        else:
            sections = []

        return DocResult(
            doc_type=doc_type,
            sections=sections,
            output_path=self.config.output,
            generated_at=datetime.now().isoformat(),
        )

    def format_result(self, result: DocResult, format: str = "text") -> str:
        """Format documentation result."""
        if format == "json":
            return json.dumps(result.to_dict(), indent=2)

        if format == "markdown":
            return result.to_markdown()

        lines = [
            "Documentation Generated",
            "=" * 40,
            f"Type: {result.doc_type}",
            f"Sections: {len(result.sections)}",
        ]

        for s in result.sections:
            lines.append(f"  - {s.title}")

        return "\n".join(lines)


__all__ = [
    "DocType",
    "DocConfig",
    "DocSection",
    "DocResult",
    "APIDocGenerator",
    "ReadmeGenerator",
    "ArchitectureGenerator",
    "DocumentCommand",
]
