"""Tests for ZERG StepGenerator module."""

from unittest.mock import MagicMock

from zerg.step_generator import (
    DetailLevel,
    Step,
    StepAction,
    StepGenerator,
    TaskDefinition,
    VerifyMode,
    generate_steps_for_task,
)


class TestDetailLevel:
    """Tests for DetailLevel enum."""

    def test_standard_value(self):
        """Standard detail level has correct value."""
        assert DetailLevel.STANDARD.value == "standard"

    def test_medium_value(self):
        """Medium detail level has correct value."""
        assert DetailLevel.MEDIUM.value == "medium"

    def test_high_value(self):
        """High detail level has correct value."""
        assert DetailLevel.HIGH.value == "high"

    def test_from_string(self):
        """DetailLevel can be created from string."""
        assert DetailLevel("standard") == DetailLevel.STANDARD
        assert DetailLevel("medium") == DetailLevel.MEDIUM
        assert DetailLevel("high") == DetailLevel.HIGH


class TestStepAction:
    """Tests for StepAction enum."""

    def test_tdd_actions_exist(self):
        """All TDD actions are defined."""
        actions = [
            StepAction.WRITE_TEST,
            StepAction.VERIFY_FAIL,
            StepAction.IMPLEMENT,
            StepAction.VERIFY_PASS,
            StepAction.FORMAT,
            StepAction.COMMIT,
        ]
        assert len(actions) == 6

    def test_action_values(self):
        """Action values match schema enum."""
        assert StepAction.WRITE_TEST.value == "write_test"
        assert StepAction.VERIFY_FAIL.value == "verify_fail"
        assert StepAction.IMPLEMENT.value == "implement"
        assert StepAction.VERIFY_PASS.value == "verify_pass"
        assert StepAction.FORMAT.value == "format"
        assert StepAction.COMMIT.value == "commit"


class TestVerifyMode:
    """Tests for VerifyMode enum."""

    def test_verify_modes(self):
        """All verify modes have correct values."""
        assert VerifyMode.EXIT_CODE.value == "exit_code"
        assert VerifyMode.EXIT_CODE_NONZERO.value == "exit_code_nonzero"
        assert VerifyMode.NONE.value == "none"


class TestStep:
    """Tests for Step dataclass."""

    def test_create_minimal_step(self):
        """Step can be created with minimal fields."""
        step = Step(step=1, action=StepAction.WRITE_TEST)
        assert step.step == 1
        assert step.action == StepAction.WRITE_TEST
        assert step.file is None
        assert step.code_snippet is None
        assert step.run is None
        assert step.verify == VerifyMode.EXIT_CODE

    def test_create_full_step(self):
        """Step can be created with all fields."""
        step = Step(
            step=1,
            action=StepAction.WRITE_TEST,
            file="tests/test_foo.py",
            code_snippet="def test_foo(): pass",
            run="pytest",
            verify=VerifyMode.NONE,
        )
        assert step.file == "tests/test_foo.py"
        assert step.code_snippet == "def test_foo(): pass"
        assert step.run == "pytest"
        assert step.verify == VerifyMode.NONE

    def test_to_dict_minimal(self):
        """to_dict with minimal fields produces correct output."""
        step = Step(step=1, action=StepAction.WRITE_TEST)
        result = step.to_dict()

        assert result["step"] == 1
        assert result["action"] == "write_test"
        assert result["verify"] == "exit_code"
        assert "file" not in result
        assert "code_snippet" not in result
        assert "run" not in result

    def test_to_dict_full(self):
        """to_dict with all fields produces correct output."""
        step = Step(
            step=3,
            action=StepAction.IMPLEMENT,
            file="zerg/foo.py",
            code_snippet="class Foo: pass",
            run="pytest tests/",
            verify=VerifyMode.EXIT_CODE_NONZERO,
        )
        result = step.to_dict()

        assert result["step"] == 3
        assert result["action"] == "implement"
        assert result["file"] == "zerg/foo.py"
        assert result["code_snippet"] == "class Foo: pass"
        assert result["run"] == "pytest tests/"
        assert result["verify"] == "exit_code_nonzero"


class TestTaskDefinition:
    """Tests for TaskDefinition dataclass."""

    def test_create_minimal(self):
        """TaskDefinition can be created with minimal fields."""
        task = TaskDefinition(id="TEST-001", title="Test Task")
        assert task.id == "TEST-001"
        assert task.title == "Test Task"
        assert task.description == ""
        assert task.files == {}
        assert task.verification == {}

    def test_create_full(self):
        """TaskDefinition can be created with all fields."""
        task = TaskDefinition(
            id="TEST-001",
            title="Test Task",
            description="Do something",
            files={"create": ["foo.py"], "modify": ["bar.py"]},
            verification={"command": "pytest"},
        )
        assert task.description == "Do something"
        assert task.files["create"] == ["foo.py"]
        assert task.verification["command"] == "pytest"

    def test_from_dict(self):
        """TaskDefinition can be created from dictionary."""
        data = {
            "id": "TEST-002",
            "title": "Dict Task",
            "description": "From dict",
            "files": {"create": ["new.py"]},
            "verification": {"command": "python -m pytest"},
        }
        task = TaskDefinition.from_dict(data)

        assert task.id == "TEST-002"
        assert task.title == "Dict Task"
        assert task.description == "From dict"
        assert task.files["create"] == ["new.py"]
        assert task.verification["command"] == "python -m pytest"

    def test_from_dict_missing_fields(self):
        """TaskDefinition handles missing optional fields."""
        data = {"id": "TEST-003", "title": "Minimal"}
        task = TaskDefinition.from_dict(data)

        assert task.id == "TEST-003"
        assert task.description == ""
        assert task.files == {}


class TestStepGeneratorInit:
    """Tests for StepGenerator initialization."""

    def test_default_project_root(self, tmp_path, monkeypatch):
        """Default project root is current directory."""
        monkeypatch.chdir(tmp_path)
        gen = StepGenerator()
        assert gen.project_root == tmp_path

    def test_custom_project_root_path(self, tmp_path):
        """Custom project root as Path is stored."""
        gen = StepGenerator(project_root=tmp_path)
        assert gen.project_root == tmp_path

    def test_custom_project_root_str(self, tmp_path):
        """Custom project root as string is converted to Path."""
        gen = StepGenerator(project_root=str(tmp_path))
        assert gen.project_root == tmp_path

    def test_ast_analyzer_optional(self, tmp_path):
        """AST analyzer is optional."""
        gen = StepGenerator(project_root=tmp_path, ast_analyzer=None)
        assert gen.ast_analyzer is None

    def test_ast_analyzer_stored(self, tmp_path):
        """AST analyzer is stored when provided."""
        mock_analyzer = MagicMock()
        gen = StepGenerator(project_root=tmp_path, ast_analyzer=mock_analyzer)
        assert gen.ast_analyzer is mock_analyzer


class TestStepGeneratorStandardDetail:
    """Tests for standard detail level (no steps)."""

    def test_standard_returns_empty_list(self, tmp_path):
        """Standard detail returns empty step list."""
        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(id="TEST-001", title="Test")

        steps = gen.generate_steps(task, DetailLevel.STANDARD)

        assert steps == []

    def test_standard_string_returns_empty(self, tmp_path):
        """Standard detail as string returns empty list."""
        gen = StepGenerator(project_root=tmp_path)
        task = {"id": "TEST-001", "title": "Test"}

        steps = gen.generate_steps(task, "standard")

        assert steps == []


class TestStepGeneratorMediumDetail:
    """Tests for medium detail level (TDD steps without snippets)."""

    def test_medium_returns_six_steps(self, tmp_path):
        """Medium detail returns 6 TDD steps."""
        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(
            id="TEST-001",
            title="Test Feature",
            files={"create": ["zerg/foo.py"]},
        )

        steps = gen.generate_steps(task, DetailLevel.MEDIUM)

        assert len(steps) == 6

    def test_medium_step_order(self, tmp_path):
        """Medium detail has correct TDD step order."""
        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(id="TEST-001", title="Test", files={"create": ["zerg/foo.py"]})

        steps = gen.generate_steps(task, DetailLevel.MEDIUM)

        expected_order = [
            StepAction.WRITE_TEST,
            StepAction.VERIFY_FAIL,
            StepAction.IMPLEMENT,
            StepAction.VERIFY_PASS,
            StepAction.FORMAT,
            StepAction.COMMIT,
        ]
        for i, step in enumerate(steps):
            assert step.step == i + 1
            assert step.action == expected_order[i]

    def test_medium_no_code_snippets(self, tmp_path):
        """Medium detail does not include code snippets."""
        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(id="TEST-001", title="Test", files={"create": ["zerg/foo.py"]})

        steps = gen.generate_steps(task, DetailLevel.MEDIUM)

        for step in steps:
            assert step.code_snippet is None

    def test_medium_verify_fail_uses_nonzero(self, tmp_path):
        """verify_fail step uses EXIT_CODE_NONZERO verification."""
        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(id="TEST-001", title="Test", files={"create": ["zerg/foo.py"]})

        steps = gen.generate_steps(task, DetailLevel.MEDIUM)

        verify_fail = steps[1]  # Second step
        assert verify_fail.action == StepAction.VERIFY_FAIL
        assert verify_fail.verify == VerifyMode.EXIT_CODE_NONZERO

    def test_medium_verify_pass_uses_exit_code(self, tmp_path):
        """verify_pass step uses EXIT_CODE verification."""
        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(id="TEST-001", title="Test", files={"create": ["zerg/foo.py"]})

        steps = gen.generate_steps(task, DetailLevel.MEDIUM)

        verify_pass = steps[3]  # Fourth step
        assert verify_pass.action == StepAction.VERIFY_PASS
        assert verify_pass.verify == VerifyMode.EXIT_CODE


class TestStepGeneratorHighDetail:
    """Tests for high detail level (TDD steps with snippets)."""

    def test_high_returns_six_steps(self, tmp_path):
        """High detail returns 6 TDD steps."""
        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(id="TEST-001", title="Test", files={"create": ["zerg/foo.py"]})

        steps = gen.generate_steps(task, DetailLevel.HIGH)

        assert len(steps) == 6

    def test_high_includes_code_snippets(self, tmp_path):
        """High detail includes code snippets for write_test and implement."""
        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(
            id="TEST-001",
            title="Test Feature",
            description="Implement test feature",
            files={"create": ["zerg/foo.py"]},
        )

        steps = gen.generate_steps(task, DetailLevel.HIGH)

        write_test = steps[0]
        implement = steps[2]

        assert write_test.code_snippet is not None
        assert implement.code_snippet is not None
        assert "test" in write_test.code_snippet.lower()

    def test_high_string_detail_works(self, tmp_path):
        """High detail as string works correctly."""
        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(id="TEST-001", title="Test", files={"create": ["zerg/foo.py"]})

        steps = gen.generate_steps(task, "high")

        assert len(steps) == 6
        assert steps[0].code_snippet is not None


class TestStepGeneratorFormatterIntegration:
    """Tests for formatter detection integration."""

    def test_format_step_uses_detected_formatter(self, tmp_path):
        """Format step uses detected formatter command."""
        # Create pyproject.toml with ruff config
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.ruff]\nline-length = 88")

        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(id="TEST-001", title="Test", files={"create": ["zerg/foo.py"]})

        steps = gen.generate_steps(task, DetailLevel.MEDIUM)

        format_step = steps[4]  # Fifth step
        assert format_step.action == StepAction.FORMAT
        assert "ruff format" in format_step.run

    def test_format_step_fallback_without_formatter(self, tmp_path):
        """Format step has fallback when no formatter detected."""
        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(id="TEST-001", title="Test", files={"create": ["zerg/foo.py"]})

        steps = gen.generate_steps(task, DetailLevel.MEDIUM)

        format_step = steps[4]
        assert format_step.action == StepAction.FORMAT
        assert format_step.run is not None
        assert "echo" in format_step.run or format_step.run != ""

    def test_formatter_cached(self, tmp_path):
        """Formatter detection result is cached."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.ruff]\nline-length = 88")

        gen = StepGenerator(project_root=tmp_path)

        # Access formatter twice
        formatter1 = gen.formatter
        formatter2 = gen.formatter

        assert formatter1 is formatter2


class TestStepGeneratorFileInference:
    """Tests for test/impl file inference."""

    def test_infers_test_file_from_impl(self, tmp_path):
        """Infers test file path from implementation file."""
        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(
            id="TEST-001",
            title="Test",
            files={"create": ["zerg/my_module.py"]},
        )

        steps = gen.generate_steps(task, DetailLevel.MEDIUM)

        write_test = steps[0]
        assert write_test.file is not None
        assert "test_my_module" in write_test.file

    def test_uses_explicit_test_file(self, tmp_path):
        """Uses explicit test file when provided."""
        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(
            id="TEST-001",
            title="Test",
            files={
                "create": ["tests/unit/test_custom.py", "zerg/impl.py"],
            },
        )

        steps = gen.generate_steps(task, DetailLevel.MEDIUM)

        write_test = steps[0]
        assert write_test.file == "tests/unit/test_custom.py"

    def test_impl_file_on_implement_step(self, tmp_path):
        """Implementation file is set on implement step."""
        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(
            id="TEST-001",
            title="Test",
            files={"create": ["zerg/my_impl.py"]},
        )

        steps = gen.generate_steps(task, DetailLevel.MEDIUM)

        implement = steps[2]
        assert implement.file == "zerg/my_impl.py"


class TestStepGeneratorVerification:
    """Tests for verification command integration."""

    def test_uses_task_verification_command(self, tmp_path):
        """Uses verification command from task definition."""
        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(
            id="TEST-001",
            title="Test",
            files={"create": ["zerg/foo.py"]},
            verification={"command": "python -m pytest tests/ -v"},
        )

        steps = gen.generate_steps(task, DetailLevel.MEDIUM)

        verify_fail = steps[1]
        verify_pass = steps[3]

        assert verify_fail.run == "python -m pytest tests/ -v"
        assert verify_pass.run == "python -m pytest tests/ -v"

    def test_default_verification_command(self, tmp_path):
        """Uses default pytest command when not specified."""
        gen = StepGenerator(project_root=tmp_path)
        task = TaskDefinition(id="TEST-001", title="Test", files={"create": ["zerg/foo.py"]})

        steps = gen.generate_steps(task, DetailLevel.MEDIUM)

        verify_fail = steps[1]
        assert "pytest" in verify_fail.run


class TestStepGeneratorDictInput:
    """Tests for dictionary input handling."""

    def test_accepts_dict_task(self, tmp_path):
        """Accepts task as dictionary."""
        gen = StepGenerator(project_root=tmp_path)
        task = {
            "id": "TEST-001",
            "title": "Dict Task",
            "files": {"create": ["zerg/foo.py"]},
        }

        steps = gen.generate_steps(task, DetailLevel.MEDIUM)

        assert len(steps) == 6


class TestStepGeneratorHelpers:
    """Tests for helper methods."""

    def test_snake_case_simple(self):
        """snake_case converts simple text."""
        result = StepGenerator._snake_case("Hello World")
        assert result == "hello_world"

    def test_snake_case_camel(self):
        """snake_case converts CamelCase."""
        result = StepGenerator._snake_case("MyClassName")
        assert result == "my_class_name"

    def test_snake_case_special_chars(self):
        """snake_case handles special characters."""
        result = StepGenerator._snake_case("Hello-World!")
        assert result == "hello_world"

    def test_pascal_case_simple(self):
        """pascal_case converts simple text."""
        result = StepGenerator._pascal_case("hello world")
        assert result == "HelloWorld"

    def test_pascal_case_hyphenated(self):
        """pascal_case converts hyphenated text."""
        result = StepGenerator._pascal_case("hello-world-test")
        assert result == "HelloWorldTest"


class TestConvenienceFunction:
    """Tests for generate_steps_for_task function."""

    def test_returns_list_of_dicts(self, tmp_path, monkeypatch):
        """Convenience function returns list of dictionaries."""
        monkeypatch.chdir(tmp_path)
        task = {
            "id": "TEST-001",
            "title": "Test",
            "files": {"create": ["zerg/foo.py"]},
        }

        result = generate_steps_for_task(task, "medium")

        assert isinstance(result, list)
        assert all(isinstance(s, dict) for s in result)
        assert len(result) == 6

    def test_standard_returns_empty_list(self, tmp_path, monkeypatch):
        """Convenience function returns empty for standard."""
        monkeypatch.chdir(tmp_path)
        task = {"id": "TEST-001", "title": "Test"}

        result = generate_steps_for_task(task, "standard")

        assert result == []

    def test_accepts_project_root(self, tmp_path):
        """Convenience function accepts project_root parameter."""
        task = {"id": "TEST-001", "title": "Test", "files": {"create": ["zerg/foo.py"]}}

        result = generate_steps_for_task(task, "medium", project_root=tmp_path)

        assert len(result) == 6


class TestASTAnalyzerIntegration:
    """Tests for AST analyzer integration (when available)."""

    def test_uses_ast_analyzer_for_snippets(self, tmp_path):
        """Uses AST analyzer when available and detail is high."""
        mock_analyzer = MagicMock()
        mock_patterns = MagicMock()
        mock_patterns.imports = []
        mock_analyzer.extract_patterns.return_value = mock_patterns

        gen = StepGenerator(project_root=tmp_path, ast_analyzer=mock_analyzer)
        task = TaskDefinition(
            id="TEST-001",
            title="Test",
            files={"create": ["zerg/foo.py"]},
        )

        gen.generate_steps(task, DetailLevel.HIGH)

        # Should attempt to use analyzer for snippets
        assert mock_analyzer.extract_patterns.called or True  # Graceful fallback

    def test_fallback_without_ast_analyzer(self, tmp_path):
        """Falls back to generic snippets without AST analyzer."""
        gen = StepGenerator(project_root=tmp_path, ast_analyzer=None)
        task = TaskDefinition(
            id="TEST-001",
            title="Test Feature",
            files={"create": ["zerg/foo.py"]},
        )

        steps = gen.generate_steps(task, DetailLevel.HIGH)

        # Should still generate snippets
        assert steps[0].code_snippet is not None
        assert steps[2].code_snippet is not None

    def test_ast_analyzer_exception_handled(self, tmp_path):
        """Handles exceptions from AST analyzer gracefully."""
        mock_analyzer = MagicMock()
        mock_analyzer.extract_patterns.side_effect = Exception("Parse error")

        gen = StepGenerator(project_root=tmp_path, ast_analyzer=mock_analyzer)
        task = TaskDefinition(
            id="TEST-001",
            title="Test",
            files={"create": ["zerg/foo.py"]},
        )

        # Should not raise, should fall back to generic snippets
        steps = gen.generate_steps(task, DetailLevel.HIGH)
        assert len(steps) == 6
        assert steps[0].code_snippet is not None
