"""Tests for ZERG v2 Document Command."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDocType:
    """Tests for DocType enum."""

    def test_doc_types_exist(self):
        """Test documentation types are defined."""
        from document import DocType

        assert hasattr(DocType, "API")
        assert hasattr(DocType, "README")
        assert hasattr(DocType, "ARCHITECTURE")
        assert hasattr(DocType, "CHANGELOG")


class TestDocSection:
    """Tests for DocSection dataclass."""

    def test_section_creation(self):
        """Test DocSection can be created."""
        from document import DocSection

        section = DocSection(title="Overview", content="Some content")
        assert section.title == "Overview"
        assert section.content == "Some content"

    def test_section_to_markdown(self):
        """Test DocSection markdown conversion."""
        from document import DocSection

        section = DocSection(title="Test", content="Content", level=2)
        md = section.to_markdown()
        assert md.startswith("## Test")
        assert "Content" in md


class TestDocResult:
    """Tests for DocResult dataclass."""

    def test_result_creation(self):
        """Test DocResult can be created."""
        from document import DocResult, DocSection

        sections = [DocSection(title="Intro", content="Hello")]
        result = DocResult(doc_type="api", sections=sections)
        assert result.doc_type == "api"
        assert len(result.sections) == 1

    def test_result_to_dict(self):
        """Test DocResult serialization."""
        from document import DocResult, DocSection

        sections = [DocSection(title="Test", content="Content")]
        result = DocResult(doc_type="readme", sections=sections)
        data = result.to_dict()
        assert data["doc_type"] == "readme"

    def test_result_to_markdown(self):
        """Test DocResult full markdown output."""
        from document import DocResult, DocSection

        sections = [
            DocSection(title="Title", content="Content", level=1),
            DocSection(title="Sub", content="More", level=2),
        ]
        result = DocResult(doc_type="api", sections=sections)
        md = result.to_markdown()
        assert "# Title" in md
        assert "## Sub" in md


class TestAPIDocGenerator:
    """Tests for APIDocGenerator."""

    def test_generator_creation(self):
        """Test APIDocGenerator can be created."""
        from document import APIDocGenerator

        gen = APIDocGenerator()
        assert gen is not None

    def test_generate_returns_sections(self):
        """Test generate returns DocSection list."""
        from document import APIDocGenerator

        gen = APIDocGenerator()
        sections = gen.generate([])
        assert len(sections) >= 1
        assert sections[0].title == "API Reference"


class TestReadmeGenerator:
    """Tests for ReadmeGenerator."""

    def test_generator_creation(self):
        """Test ReadmeGenerator can be created."""
        from document import ReadmeGenerator

        gen = ReadmeGenerator()
        assert gen is not None

    def test_generate_has_sections(self):
        """Test generate includes standard sections."""
        from document import ReadmeGenerator

        gen = ReadmeGenerator()
        sections = gen.generate(Path("."))
        titles = [s.title for s in sections]
        assert "Installation" in titles
        assert "Usage" in titles


class TestArchitectureGenerator:
    """Tests for ArchitectureGenerator."""

    def test_generator_creation(self):
        """Test ArchitectureGenerator can be created."""
        from document import ArchitectureGenerator

        gen = ArchitectureGenerator()
        assert gen is not None

    def test_generate_with_diagram(self):
        """Test generate includes mermaid diagram."""
        from document import ArchitectureGenerator

        gen = ArchitectureGenerator()
        sections = gen.generate(Path("."), diagram=True)
        titles = [s.title for s in sections]
        assert "Architecture Diagram" in titles


class TestDocumentCommand:
    """Tests for DocumentCommand."""

    def test_command_creation(self):
        """Test DocumentCommand can be created."""
        from document import DocumentCommand

        cmd = DocumentCommand()
        assert cmd is not None

    def test_command_run_api(self):
        """Test running API documentation generation."""
        from document import DocResult, DocumentCommand

        cmd = DocumentCommand()
        result = cmd.run(doc_type="api", dry_run=True)
        assert isinstance(result, DocResult)
        assert result.doc_type == "api"

    def test_command_run_readme(self):
        """Test running README generation."""
        from document import DocumentCommand

        cmd = DocumentCommand()
        result = cmd.run(doc_type="readme")
        assert result.doc_type == "readme"
