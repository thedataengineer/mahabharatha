"""Tests for ZERG v2 Explain Command."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAudience:
    """Tests for Audience enum."""

    def test_audience_levels_exist(self):
        """Test audience levels are defined."""
        from explain import Audience

        assert hasattr(Audience, "BEGINNER")
        assert hasattr(Audience, "INTERMEDIATE")
        assert hasattr(Audience, "EXPERT")


class TestExplainDepth:
    """Tests for ExplainDepth enum."""

    def test_depth_levels_exist(self):
        """Test depth levels are defined."""
        from explain import ExplainDepth

        assert hasattr(ExplainDepth, "SUMMARY")
        assert hasattr(ExplainDepth, "DETAILED")
        assert hasattr(ExplainDepth, "COMPREHENSIVE")


class TestExplainConfig:
    """Tests for ExplainConfig dataclass."""

    def test_config_defaults(self):
        """Test ExplainConfig default values."""
        from explain import ExplainConfig

        config = ExplainConfig()
        assert config.audience == "intermediate"
        assert config.depth == "detailed"
        assert config.include_diagram is True

    def test_config_custom(self):
        """Test ExplainConfig with custom values."""
        from explain import ExplainConfig

        config = ExplainConfig(audience="beginner", depth="summary")
        assert config.audience == "beginner"
        assert config.depth == "summary"


class TestCodeReference:
    """Tests for CodeReference dataclass."""

    def test_reference_creation(self):
        """Test CodeReference can be created."""
        from explain import CodeReference

        ref = CodeReference(file="test.py", line=10, name="func", ref_type="caller")
        assert ref.file == "test.py"
        assert ref.line == 10

    def test_reference_to_dict(self):
        """Test CodeReference serialization."""
        from explain import CodeReference

        ref = CodeReference(file="a.py", line=5, name="foo", ref_type="callee")
        data = ref.to_dict()
        assert data["file"] == "a.py"
        assert data["ref_type"] == "callee"


class TestExplainResult:
    """Tests for ExplainResult dataclass."""

    def test_result_creation(self):
        """Test ExplainResult can be created."""
        from explain import ExplainResult

        result = ExplainResult(
            target="test.py",
            summary="A test file",
            explanation="Details",
            audience="beginner",
            depth="summary",
        )
        assert result.target == "test.py"

    def test_result_to_dict(self):
        """Test ExplainResult serialization."""
        from explain import ExplainResult

        result = ExplainResult(
            target="test.py",
            summary="Summary",
            explanation="Explanation",
            audience="expert",
            depth="comprehensive",
        )
        data = result.to_dict()
        assert data["target"] == "test.py"
        assert data["audience"] == "expert"

    def test_result_to_markdown(self):
        """Test ExplainResult markdown output."""
        from explain import ExplainResult

        result = ExplainResult(
            target="test.py",
            summary="A test file",
            explanation="Details",
            audience="intermediate",
            depth="detailed",
        )
        md = result.to_markdown()
        assert "# test.py" in md
        assert "## Summary" in md


class TestCodeAnalyzer:
    """Tests for CodeAnalyzer."""

    def test_analyzer_creation(self):
        """Test CodeAnalyzer can be created."""
        from explain import CodeAnalyzer

        analyzer = CodeAnalyzer()
        assert analyzer is not None

    def test_analyze_nonexistent_file(self):
        """Test analyzing non-existent file."""
        from explain import CodeAnalyzer

        analyzer = CodeAnalyzer()
        result = analyzer.analyze_file(Path("/nonexistent/file.py"))
        assert "error" in result


class TestExplanationGenerator:
    """Tests for ExplanationGenerator."""

    def test_generator_creation(self):
        """Test ExplanationGenerator can be created."""
        from explain import ExplanationGenerator

        gen = ExplanationGenerator()
        assert gen is not None

    def test_explain_concept(self):
        """Test concept explanation."""
        from explain import ExplainConfig, ExplanationGenerator

        config = ExplainConfig(audience="beginner")
        gen = ExplanationGenerator(config=config)
        result = gen.explain_concept("REST API")
        assert result.target == "REST API"
        assert "beginner" in result.audience


class TestExplainCommand:
    """Tests for ExplainCommand."""

    def test_command_creation(self):
        """Test ExplainCommand can be created."""
        from explain import ExplainCommand

        cmd = ExplainCommand()
        assert cmd is not None

    def test_command_explain_concept(self):
        """Test explaining a concept."""
        from explain import ExplainCommand, ExplainResult

        cmd = ExplainCommand()
        result = cmd.run(target="JWT", target_type="concept")
        assert isinstance(result, ExplainResult)
        assert result.target == "JWT"

    def test_command_format_text(self):
        """Test text output formatting."""
        from explain import ExplainCommand, ExplainResult

        cmd = ExplainCommand()
        result = ExplainResult(
            target="test",
            summary="Summary",
            explanation="Explanation",
            audience="intermediate",
            depth="detailed",
        )
        output = cmd.format_result(result, format="text")
        assert "Explanation" in output
        assert "test" in output
