"""ZERG v2 Index Command - Project knowledge base generation."""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Symbol:
    """A code symbol (function, class, etc.)."""

    name: str
    symbol_type: str  # function, class, interface, type
    line: int
    doc: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.symbol_type,
            "line": self.line,
            "doc": self.doc,
        }


@dataclass
class FileInfo:
    """Information about a source file."""

    path: str
    language: str
    symbols: list[Symbol] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "language": self.language,
            "symbols": [s.to_dict() for s in self.symbols],
            "imports": self.imports,
            "exports": self.exports,
        }


@dataclass
class ProjectIndex:
    """Complete project index."""

    files: list[FileInfo]
    dependencies: dict[str, list[str]]
    created_at: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "files": [f.to_dict() for f in self.files],
            "dependencies": self.dependencies,
            "created_at": self.created_at,
        }


@dataclass
class IndexConfig:
    """Configuration for indexing."""

    format: str = "json"
    embeddings: bool = False
    include: list[str] = field(default_factory=lambda: ["src/**"])
    exclude: list[str] = field(default_factory=lambda: ["node_modules", "venv"])


class LanguageDetector:
    """Detect file language."""

    EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".rb": "ruby",
        ".cpp": "cpp",
        ".c": "c",
    }

    def detect(self, filepath: str) -> str:
        """Detect language from file extension."""
        ext = Path(filepath).suffix.lower()
        return self.EXTENSIONS.get(ext, "unknown")


class SymbolExtractor:
    """Extract symbols from source files."""

    def extract(self, content: str, language: str) -> list[Symbol]:
        """Extract symbols from content."""
        symbols = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            line = line.strip()

            # Python
            if language == "python":
                if line.startswith("def "):
                    name = line.split("(")[0].replace("def ", "")
                    symbols.append(Symbol(name=name, symbol_type="function", line=i))
                elif line.startswith("class "):
                    name = line.split("(")[0].split(":")[0].replace("class ", "")
                    symbols.append(Symbol(name=name, symbol_type="class", line=i))

            # TypeScript/JavaScript
            elif language in ("typescript", "javascript"):
                if "function " in line:
                    parts = line.split("function ")[1].split("(")
                    if parts:
                        symbols.append(
                            Symbol(name=parts[0].strip(), symbol_type="function", line=i)
                        )
                elif line.startswith("class "):
                    name = line.split("{")[0].replace("class ", "").strip()
                    symbols.append(Symbol(name=name, symbol_type="class", line=i))
                elif line.startswith("interface "):
                    name = line.split("{")[0].replace("interface ", "").strip()
                    symbols.append(Symbol(name=name, symbol_type="interface", line=i))

        return symbols


class Indexer:
    """Project indexer."""

    def __init__(self, config: IndexConfig | None = None):
        """Initialize indexer."""
        self.config = config or IndexConfig()
        self.detector = LanguageDetector()
        self.extractor = SymbolExtractor()

    def index_file(self, filepath: Path) -> FileInfo:
        """Index a single file."""
        language = self.detector.detect(str(filepath))

        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            content = ""

        symbols = self.extractor.extract(content, language)

        return FileInfo(
            path=str(filepath),
            language=language,
            symbols=symbols,
        )

    def index_project(self, root: Path) -> ProjectIndex:
        """Index entire project."""
        from datetime import datetime

        files = []
        dependencies: dict[str, list[str]] = {}

        # Find all source files
        for pattern in self.config.include:
            for filepath in root.glob(pattern):
                if filepath.is_file():
                    # Check exclusions
                    excluded = False
                    for exc in self.config.exclude:
                        if exc in str(filepath):
                            excluded = True
                            break
                    if not excluded:
                        files.append(self.index_file(filepath))

        return ProjectIndex(
            files=files,
            dependencies=dependencies,
            created_at=datetime.now().isoformat(),
        )


class IndexCommand:
    """Main index command orchestrator."""

    def __init__(self, config: IndexConfig | None = None):
        """Initialize index command."""
        self.config = config or IndexConfig()
        self.indexer = Indexer(config=self.config)

    def run(self, path: str = ".", dry_run: bool = False) -> ProjectIndex:
        """Run indexing."""
        if dry_run:
            return ProjectIndex(files=[], dependencies={})

        return self.indexer.index_project(Path(path))

    def format_result(self, result: ProjectIndex, format: str = "text") -> str:
        """Format index result."""
        if format == "json":
            return json.dumps(result.to_dict(), indent=2)

        lines = [
            "Project Index",
            "=" * 40,
            f"Files: {len(result.files)}",
        ]

        # Count symbols
        total_symbols = sum(len(f.symbols) for f in result.files)
        lines.append(f"Symbols: {total_symbols}")

        if result.files:
            lines.append("")
            lines.append("Files:")
            for f in result.files[:10]:
                lines.append(f"  - {f.path} ({f.language}): {len(f.symbols)} symbols")

        return "\n".join(lines)


__all__ = [
    "Symbol",
    "FileInfo",
    "ProjectIndex",
    "IndexConfig",
    "LanguageDetector",
    "SymbolExtractor",
    "Indexer",
    "IndexCommand",
]
