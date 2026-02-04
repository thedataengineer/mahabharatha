"""Tests for ZERG FormatterDetector module."""

import json

from zerg.formatter_detector import FormatterConfig, FormatterDetector, detect_formatter


class TestFormatterConfig:
    """Tests for FormatterConfig dataclass."""

    def test_create_with_all_fields(self):
        """FormatterConfig stores all fields correctly."""
        config = FormatterConfig(
            name="test",
            format_cmd="test --check",
            fix_cmd="test --fix",
            file_patterns=["*.py", "*.txt"],
        )
        assert config.name == "test"
        assert config.format_cmd == "test --check"
        assert config.fix_cmd == "test --fix"
        assert config.file_patterns == ["*.py", "*.txt"]

    def test_default_file_patterns(self):
        """FormatterConfig has empty list as default file_patterns."""
        config = FormatterConfig(
            name="test",
            format_cmd="test --check",
            fix_cmd="test --fix",
        )
        assert config.file_patterns == []


class TestFormatterDetectorInit:
    """Tests for FormatterDetector initialization."""

    def test_default_project_root(self, tmp_path, monkeypatch):
        """Default project root is current working directory."""
        monkeypatch.chdir(tmp_path)
        detector = FormatterDetector()
        assert detector.project_root == tmp_path

    def test_custom_project_root_path(self, tmp_path):
        """Custom project root as Path is stored."""
        detector = FormatterDetector(project_root=tmp_path)
        assert detector.project_root == tmp_path

    def test_custom_project_root_str(self, tmp_path):
        """Custom project root as string is converted to Path."""
        detector = FormatterDetector(project_root=str(tmp_path))
        assert detector.project_root == tmp_path


class TestRuffDetection:
    """Tests for ruff formatter detection."""

    def test_detects_ruff_from_pyproject_toml(self, tmp_path):
        """Detects ruff when [tool.ruff] exists in pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.ruff]
line-length = 88
""")
        detector = FormatterDetector(tmp_path)
        config = detector.detect()

        assert config is not None
        assert config.name == "ruff"
        assert "ruff format --check" in config.format_cmd
        assert "ruff format" in config.fix_cmd
        assert "*.py" in config.file_patterns

    def test_no_detection_without_ruff_section(self, tmp_path):
        """Does not detect ruff without [tool.ruff] section."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test"
""")
        detector = FormatterDetector(tmp_path)
        # Use the specific detector method
        config = detector._detect_ruff()
        assert config is None

    def test_no_detection_without_pyproject(self, tmp_path):
        """Does not detect ruff without pyproject.toml."""
        detector = FormatterDetector(tmp_path)
        config = detector._detect_ruff()
        assert config is None


class TestBlackDetection:
    """Tests for black formatter detection."""

    def test_detects_black_from_pyproject_toml(self, tmp_path):
        """Detects black when [tool.black] exists in pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.black]
line-length = 88
""")
        detector = FormatterDetector(tmp_path)
        config = detector._detect_black()

        assert config is not None
        assert config.name == "black"
        assert "black --check" in config.format_cmd
        assert "black" in config.fix_cmd
        assert "*.py" in config.file_patterns

    def test_no_detection_without_black_section(self, tmp_path):
        """Does not detect black without [tool.black] section."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.ruff]
line-length = 88
""")
        detector = FormatterDetector(tmp_path)
        config = detector._detect_black()
        assert config is None

    def test_ruff_takes_priority_over_black(self, tmp_path):
        """When both ruff and black are configured, ruff wins."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.ruff]
line-length = 88

[tool.black]
line-length = 88
""")
        detector = FormatterDetector(tmp_path)
        config = detector.detect()

        assert config is not None
        assert config.name == "ruff"


class TestPrettierDetection:
    """Tests for prettier formatter detection."""

    def test_detects_prettier_from_prettierrc(self, tmp_path):
        """Detects prettier from .prettierrc file."""
        prettierrc = tmp_path / ".prettierrc"
        prettierrc.write_text("{}")
        detector = FormatterDetector(tmp_path)
        config = detector._detect_prettier()

        assert config is not None
        assert config.name == "prettier"
        assert "npx prettier --check" in config.format_cmd
        assert "npx prettier --write" in config.fix_cmd
        assert "*.js" in config.file_patterns
        assert "*.ts" in config.file_patterns

    def test_detects_prettier_from_prettierrc_json(self, tmp_path):
        """Detects prettier from .prettierrc.json file."""
        prettierrc = tmp_path / ".prettierrc.json"
        prettierrc.write_text("{}")
        detector = FormatterDetector(tmp_path)
        config = detector._detect_prettier()

        assert config is not None
        assert config.name == "prettier"

    def test_detects_prettier_from_prettierrc_yml(self, tmp_path):
        """Detects prettier from .prettierrc.yml file."""
        prettierrc = tmp_path / ".prettierrc.yml"
        prettierrc.write_text("tabWidth: 2")
        detector = FormatterDetector(tmp_path)
        config = detector._detect_prettier()

        assert config is not None
        assert config.name == "prettier"

    def test_detects_prettier_from_package_json(self, tmp_path):
        """Detects prettier from package.json prettier field."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "test",
                    "prettier": {"tabWidth": 2},
                }
            )
        )
        detector = FormatterDetector(tmp_path)
        config = detector._detect_prettier()

        assert config is not None
        assert config.name == "prettier"

    def test_no_detection_without_prettier_config(self, tmp_path):
        """Does not detect prettier without configuration."""
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({"name": "test"}))
        detector = FormatterDetector(tmp_path)
        config = detector._detect_prettier()

        assert config is None

    def test_prettier_config_js_detection(self, tmp_path):
        """Detects prettier from prettier.config.js file."""
        config_js = tmp_path / "prettier.config.js"
        config_js.write_text("module.exports = {};")
        detector = FormatterDetector(tmp_path)
        config = detector._detect_prettier()

        assert config is not None
        assert config.name == "prettier"


class TestRustfmtDetection:
    """Tests for rustfmt formatter detection."""

    def test_detects_rustfmt_from_rustfmt_toml(self, tmp_path):
        """Detects rustfmt from rustfmt.toml file."""
        rustfmt = tmp_path / "rustfmt.toml"
        rustfmt.write_text("max_width = 100")
        detector = FormatterDetector(tmp_path)
        config = detector._detect_rustfmt()

        assert config is not None
        assert config.name == "rustfmt"
        assert "cargo fmt -- --check" in config.format_cmd
        assert "cargo fmt" in config.fix_cmd
        assert "*.rs" in config.file_patterns

    def test_detects_rustfmt_from_dot_rustfmt_toml(self, tmp_path):
        """Detects rustfmt from .rustfmt.toml file."""
        rustfmt = tmp_path / ".rustfmt.toml"
        rustfmt.write_text("max_width = 100")
        detector = FormatterDetector(tmp_path)
        config = detector._detect_rustfmt()

        assert config is not None
        assert config.name == "rustfmt"

    def test_no_detection_without_rustfmt_toml(self, tmp_path):
        """Does not detect rustfmt without config file."""
        detector = FormatterDetector(tmp_path)
        config = detector._detect_rustfmt()
        assert config is None


class TestClangFormatDetection:
    """Tests for clang-format formatter detection."""

    def test_detects_clang_format_from_clang_format_file(self, tmp_path):
        """Detects clang-format from .clang-format file."""
        clang_format = tmp_path / ".clang-format"
        clang_format.write_text("BasedOnStyle: Google")
        detector = FormatterDetector(tmp_path)
        config = detector._detect_clang_format()

        assert config is not None
        assert config.name == "clang-format"
        assert "clang-format" in config.format_cmd
        assert "clang-format -i" in config.fix_cmd
        assert "*.c" in config.file_patterns
        assert "*.cpp" in config.file_patterns
        assert "*.h" in config.file_patterns

    def test_detects_clang_format_from_underscore_clang_format(self, tmp_path):
        """Detects clang-format from _clang-format file."""
        clang_format = tmp_path / "_clang-format"
        clang_format.write_text("BasedOnStyle: LLVM")
        detector = FormatterDetector(tmp_path)
        config = detector._detect_clang_format()

        assert config is not None
        assert config.name == "clang-format"

    def test_no_detection_without_clang_format_file(self, tmp_path):
        """Does not detect clang-format without config file."""
        detector = FormatterDetector(tmp_path)
        config = detector._detect_clang_format()
        assert config is None


class TestGofmtDetection:
    """Tests for gofmt formatter detection."""

    def test_detects_gofmt_from_go_mod(self, tmp_path):
        """Detects gofmt from go.mod presence."""
        go_mod = tmp_path / "go.mod"
        go_mod.write_text("module example.com/test")
        detector = FormatterDetector(tmp_path)
        config = detector._detect_gofmt()

        assert config is not None
        assert config.name == "gofmt"
        assert "gofmt -l" in config.format_cmd
        assert "gofmt -w" in config.fix_cmd
        assert "*.go" in config.file_patterns

    def test_no_detection_without_go_mod(self, tmp_path):
        """Does not detect gofmt without go.mod file."""
        detector = FormatterDetector(tmp_path)
        config = detector._detect_gofmt()
        assert config is None


class TestDetectMethod:
    """Tests for the main detect() method."""

    def test_returns_none_for_empty_project(self, tmp_path):
        """Returns None when no formatter is configured."""
        detector = FormatterDetector(tmp_path)
        config = detector.detect()
        assert config is None

    def test_returns_first_matching_formatter(self, tmp_path):
        """Returns the first detected formatter based on priority."""
        # Set up ruff (highest priority) and prettier
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.ruff]\nline-length = 88")
        prettierrc = tmp_path / ".prettierrc"
        prettierrc.write_text("{}")

        detector = FormatterDetector(tmp_path)
        config = detector.detect()

        assert config is not None
        assert config.name == "ruff"


class TestDetectAllMethod:
    """Tests for the detect_all() method."""

    def test_returns_empty_list_for_empty_project(self, tmp_path):
        """Returns empty list when no formatter is configured."""
        detector = FormatterDetector(tmp_path)
        configs = detector.detect_all()
        assert configs == []

    def test_returns_all_configured_formatters(self, tmp_path):
        """Returns all detected formatters."""
        # Set up ruff and prettier
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.ruff]\nline-length = 88")
        prettierrc = tmp_path / ".prettierrc"
        prettierrc.write_text("{}")

        detector = FormatterDetector(tmp_path)
        configs = detector.detect_all()

        assert len(configs) == 2
        names = [c.name for c in configs]
        assert "ruff" in names
        assert "prettier" in names


class TestConvenienceFunction:
    """Tests for the detect_formatter convenience function."""

    def test_detect_formatter_with_project_root(self, tmp_path):
        """Convenience function works with explicit project root."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.ruff]\nline-length = 88")

        config = detect_formatter(tmp_path)
        assert config is not None
        assert config.name == "ruff"

    def test_detect_formatter_returns_none(self, tmp_path):
        """Convenience function returns None when no formatter found."""
        config = detect_formatter(tmp_path)
        assert config is None


class TestErrorHandling:
    """Tests for error handling in formatter detection."""

    def test_handles_malformed_pyproject_toml(self, tmp_path):
        """Gracefully handles malformed pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("this is not valid toml {{{")
        detector = FormatterDetector(tmp_path)

        # Should not raise, just return None
        config = detector._detect_ruff()
        assert config is None

    def test_handles_malformed_package_json(self, tmp_path):
        """Gracefully handles malformed package.json."""
        package_json = tmp_path / "package.json"
        package_json.write_text("not valid json")
        detector = FormatterDetector(tmp_path)

        # Should not raise, just return None
        config = detector._detect_prettier()
        assert config is None
