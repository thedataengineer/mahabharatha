"""Tests for MAHABHARATHA v2 Init Generator."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestProjectDetector:
    """Tests for project type detection."""

    def test_detect_python_project(self, tmp_path):
        """Test detecting Python project."""
        from init_generator import ProjectDetector

        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'")
        detector = ProjectDetector(tmp_path)
        result = detector.detect()
        assert result.language == "python"

    def test_detect_python_requirements(self, tmp_path):
        """Test detecting Python via requirements.txt."""
        from init_generator import ProjectDetector

        (tmp_path / "requirements.txt").write_text("flask\npytest")
        detector = ProjectDetector(tmp_path)
        result = detector.detect()
        assert result.language == "python"

    def test_detect_nodejs_project(self, tmp_path):
        """Test detecting Node.js project."""
        from init_generator import ProjectDetector

        (tmp_path / "package.json").write_text('{"name": "test"}')
        detector = ProjectDetector(tmp_path)
        result = detector.detect()
        assert result.language == "typescript"

    def test_detect_go_project(self, tmp_path):
        """Test detecting Go project."""
        from init_generator import ProjectDetector

        (tmp_path / "go.mod").write_text("module test")
        detector = ProjectDetector(tmp_path)
        result = detector.detect()
        assert result.language == "go"

    def test_detect_rust_project(self, tmp_path):
        """Test detecting Rust project."""
        from init_generator import ProjectDetector

        (tmp_path / "Cargo.toml").write_text("[package]\nname='test'")
        detector = ProjectDetector(tmp_path)
        result = detector.detect()
        assert result.language == "rust"

    def test_detect_unknown_project(self, tmp_path):
        """Test unknown project type."""
        from init_generator import ProjectDetector

        detector = ProjectDetector(tmp_path)
        result = detector.detect()
        assert result.language == "unknown"


class TestFrameworkDetection:
    """Tests for framework detection."""

    def test_detect_fastapi(self, tmp_path):
        """Test detecting FastAPI framework."""
        from init_generator import ProjectDetector

        (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn")
        detector = ProjectDetector(tmp_path)
        result = detector.detect()
        assert result.framework == "fastapi"

    def test_detect_flask(self, tmp_path):
        """Test detecting Flask framework."""
        from init_generator import ProjectDetector

        (tmp_path / "requirements.txt").write_text("flask\ngunicorn")
        detector = ProjectDetector(tmp_path)
        result = detector.detect()
        assert result.framework == "flask"

    def test_detect_react(self, tmp_path):
        """Test detecting React framework."""
        from init_generator import ProjectDetector

        pkg = {"name": "test", "dependencies": {"react": "^18.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        detector = ProjectDetector(tmp_path)
        result = detector.detect()
        assert result.framework == "react"

    def test_detect_nextjs(self, tmp_path):
        """Test detecting Next.js framework."""
        from init_generator import ProjectDetector

        pkg = {"name": "test", "dependencies": {"next": "^14.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        detector = ProjectDetector(tmp_path)
        result = detector.detect()
        assert result.framework == "nextjs"


class TestProjectInfo:
    """Tests for ProjectInfo dataclass."""

    def test_project_info_creation(self):
        """Test ProjectInfo can be created."""
        from init_generator import ProjectInfo

        info = ProjectInfo(
            language="python",
            framework="fastapi",
            package_manager="pip",
        )
        assert info.language == "python"
        assert info.framework == "fastapi"
        assert info.package_manager == "pip"


class TestConfigGenerator:
    """Tests for config.json generation."""

    def test_generate_config(self, tmp_path):
        """Test generating config.json."""
        from init_generator import ConfigGenerator, ProjectInfo

        info = ProjectInfo(
            language="python",
            framework="fastapi",
            package_manager="pip",
        )
        generator = ConfigGenerator(tmp_path, info)
        config = generator.generate()

        assert config["version"] == "2.0.0"
        assert config["project"]["language"] == "python"
        assert config["project"]["framework"] == "fastapi"
        assert "orchestrator" in config
        assert "quality_gates" in config

    def test_config_has_orchestrator_defaults(self, tmp_path):
        """Test config has orchestrator defaults."""
        from init_generator import ConfigGenerator, ProjectInfo

        info = ProjectInfo(language="python")
        generator = ConfigGenerator(tmp_path, info)
        config = generator.generate()

        assert config["orchestrator"]["max_workers"] == 5
        assert config["orchestrator"]["heartbeat_interval"] == 30
        assert config["orchestrator"]["context_threshold"] == 0.70


class TestInitGenerator:
    """Tests for InitGenerator class."""

    def test_init_generator_creates_structure(self, tmp_path):
        """Test InitGenerator creates .mahabharatha directory structure."""
        from init_generator import InitGenerator

        gen = InitGenerator(tmp_path)
        gen.generate()

        assert (tmp_path / ".mahabharatha").is_dir()
        assert (tmp_path / ".mahabharatha" / "config.json").exists()
        assert (tmp_path / ".mahabharatha" / "schemas").is_dir()
        assert (tmp_path / ".mahabharatha" / "templates").is_dir()
        assert (tmp_path / ".mahabharatha" / "logs").is_dir()

    def test_init_generator_creates_valid_config(self, tmp_path):
        """Test InitGenerator creates valid JSON config."""
        from init_generator import InitGenerator

        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'")
        gen = InitGenerator(tmp_path)
        gen.generate()

        config_path = tmp_path / ".mahabharatha" / "config.json"
        config = json.loads(config_path.read_text())
        assert config["version"] == "2.0.0"
        assert config["project"]["language"] == "python"

    def test_init_generator_copies_schemas(self, tmp_path):
        """Test InitGenerator copies schema files."""
        from init_generator import InitGenerator

        gen = InitGenerator(tmp_path)
        gen.generate()

        schemas_dir = tmp_path / ".mahabharatha" / "schemas"
        # Should have at least one schema file
        schema_files = list(schemas_dir.glob("*.json"))
        assert len(schema_files) >= 1

    def test_init_generator_copies_templates(self, tmp_path):
        """Test InitGenerator copies template files."""
        from init_generator import InitGenerator

        gen = InitGenerator(tmp_path)
        gen.generate()

        templates_dir = tmp_path / ".mahabharatha" / "templates"
        # Should have at least one template file
        template_files = list(templates_dir.glob("*.md"))
        assert len(template_files) >= 1

    def test_init_generator_idempotent(self, tmp_path):
        """Test InitGenerator is idempotent."""
        from init_generator import InitGenerator

        gen = InitGenerator(tmp_path)
        gen.generate()
        gen.generate()  # Should not raise

        assert (tmp_path / ".mahabharatha" / "config.json").exists()


class TestPackageManagerDetection:
    """Tests for package manager detection."""

    def test_detect_pip(self, tmp_path):
        """Test detecting pip."""
        from init_generator import ProjectDetector

        (tmp_path / "requirements.txt").write_text("flask")
        detector = ProjectDetector(tmp_path)
        result = detector.detect()
        assert result.package_manager == "pip"

    def test_detect_npm(self, tmp_path):
        """Test detecting npm."""
        from init_generator import ProjectDetector

        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "package-lock.json").write_text("{}")
        detector = ProjectDetector(tmp_path)
        result = detector.detect()
        assert result.package_manager == "npm"

    def test_detect_pnpm(self, tmp_path):
        """Test detecting pnpm."""
        from init_generator import ProjectDetector

        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "pnpm-lock.yaml").write_text("")
        detector = ProjectDetector(tmp_path)
        result = detector.detect()
        assert result.package_manager == "pnpm"

    def test_detect_cargo(self, tmp_path):
        """Test detecting cargo."""
        from init_generator import ProjectDetector

        (tmp_path / "Cargo.toml").write_text("[package]\nname='test'")
        detector = ProjectDetector(tmp_path)
        result = detector.detect()
        assert result.package_manager == "cargo"
