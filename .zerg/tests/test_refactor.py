"""Tests for ZERG v2 Refactor Command."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTransformType:
    """Tests for transform type enumeration."""

    def test_types_exist(self):
        """Test transform types are defined."""
        from refactor import TransformType

        assert hasattr(TransformType, "DEAD_CODE")
        assert hasattr(TransformType, "SIMPLIFY")
        assert hasattr(TransformType, "TYPES")
        assert hasattr(TransformType, "NAMING")


class TestRefactorConfig:
    """Tests for refactor configuration."""

    def test_config_defaults(self):
        """Test RefactorConfig has sensible defaults."""
        from refactor import RefactorConfig

        config = RefactorConfig()
        assert config.dry_run is False
        assert config.interactive is False

    def test_config_custom(self):
        """Test RefactorConfig with custom values."""
        from refactor import RefactorConfig

        config = RefactorConfig(dry_run=True, interactive=True)
        assert config.dry_run is True
        assert config.interactive is True


class TestRefactorSuggestion:
    """Tests for refactor suggestions."""

    def test_suggestion_creation(self):
        """Test RefactorSuggestion can be created."""
        from refactor import RefactorSuggestion, TransformType

        suggestion = RefactorSuggestion(
            transform_type=TransformType.DEAD_CODE,
            file="test.py",
            line=10,
            original="unused_var = 1",
            suggested="# removed",
            reason="Variable never used",
        )
        assert suggestion.transform_type == TransformType.DEAD_CODE

    def test_suggestion_to_dict(self):
        """Test RefactorSuggestion serialization."""
        from refactor import RefactorSuggestion, TransformType

        suggestion = RefactorSuggestion(
            transform_type=TransformType.SIMPLIFY,
            file="test.py",
            line=5,
            original="if x == True:",
            suggested="if x:",
            reason="Simplify boolean comparison",
        )
        data = suggestion.to_dict()
        assert data["transform"] == "simplify"
        assert data["line"] == 5


class TestRefactorResult:
    """Tests for refactor results."""

    def test_result_creation(self):
        """Test RefactorResult can be created."""
        from refactor import RefactorResult

        result = RefactorResult(
            files_analyzed=10,
            suggestions=[],
            applied=0,
        )
        assert result.files_analyzed == 10

    def test_result_with_suggestions(self):
        """Test RefactorResult with suggestions."""
        from refactor import RefactorResult, RefactorSuggestion, TransformType

        suggestion = RefactorSuggestion(
            transform_type=TransformType.NAMING,
            file="test.py",
            line=1,
            original="def x():",
            suggested="def calculate():",
            reason="More descriptive name",
        )
        result = RefactorResult(
            files_analyzed=5,
            suggestions=[suggestion],
            applied=0,
        )
        assert len(result.suggestions) == 1


class TestDeadCodeTransform:
    """Tests for dead code removal transform."""

    def test_transform_creation(self):
        """Test DeadCodeTransform can be created."""
        from refactor import DeadCodeTransform

        transform = DeadCodeTransform()
        assert transform is not None

    def test_transform_name(self):
        """Test DeadCodeTransform has correct name."""
        from refactor import DeadCodeTransform

        transform = DeadCodeTransform()
        assert transform.name == "dead-code"


class TestSimplifyTransform:
    """Tests for code simplification transform."""

    def test_transform_creation(self):
        """Test SimplifyTransform can be created."""
        from refactor import SimplifyTransform

        transform = SimplifyTransform()
        assert transform is not None

    def test_transform_name(self):
        """Test SimplifyTransform has correct name."""
        from refactor import SimplifyTransform

        transform = SimplifyTransform()
        assert transform.name == "simplify"


class TestTypesTransform:
    """Tests for type strengthening transform."""

    def test_transform_creation(self):
        """Test TypesTransform can be created."""
        from refactor import TypesTransform

        transform = TypesTransform()
        assert transform is not None

    def test_transform_name(self):
        """Test TypesTransform has correct name."""
        from refactor import TypesTransform

        transform = TypesTransform()
        assert transform.name == "types"


class TestNamingTransform:
    """Tests for naming improvement transform."""

    def test_transform_creation(self):
        """Test NamingTransform can be created."""
        from refactor import NamingTransform

        transform = NamingTransform()
        assert transform is not None

    def test_transform_name(self):
        """Test NamingTransform has correct name."""
        from refactor import NamingTransform

        transform = NamingTransform()
        assert transform.name == "naming"


class TestRefactorCommand:
    """Tests for RefactorCommand class."""

    def test_command_creation(self):
        """Test RefactorCommand can be created."""
        from refactor import RefactorCommand

        cmd = RefactorCommand()
        assert cmd is not None

    def test_command_supported_transforms(self):
        """Test RefactorCommand lists supported transforms."""
        from refactor import RefactorCommand

        cmd = RefactorCommand()
        transforms = cmd.supported_transforms()
        assert "dead-code" in transforms
        assert "simplify" in transforms

    def test_command_run_returns_result(self):
        """Test run returns RefactorResult."""
        from refactor import RefactorCommand, RefactorResult

        cmd = RefactorCommand()
        result = cmd.run(files=[], transforms=["dead-code"], dry_run=True)
        assert isinstance(result, RefactorResult)

    def test_command_format_text(self):
        """Test text output format."""
        from refactor import RefactorCommand, RefactorResult

        cmd = RefactorCommand()
        result = RefactorResult(files_analyzed=5, suggestions=[], applied=0)
        output = cmd.format_result(result, format="text")
        assert "Refactor" in output

    def test_command_format_json(self):
        """Test JSON output format."""
        import json

        from refactor import RefactorCommand, RefactorResult

        cmd = RefactorCommand()
        result = RefactorResult(files_analyzed=5, suggestions=[], applied=0)
        output = cmd.format_result(result, format="json")
        data = json.loads(output)
        assert data["files_analyzed"] == 5
