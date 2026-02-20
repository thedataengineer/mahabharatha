# DC-005: Update .mahabharatha/devcontainer.py for Multi-Language

**Level**: 3 | **Critical Path**: No | **Estimate**: 25 min
**Dependencies**: DC-003

## Objective

Update the `DevcontainerGenerator` class in `.mahabharatha/devcontainer.py` to support multi-language projects via features, maintaining backwards compatibility with single-language usage.

## Files Owned

- `.mahabharatha/devcontainer.py` (modify)

## Files to Read

- `mahabharatha/devcontainer_features.py` (reference feature mappings)

## Implementation

Update `DevcontainerGenerator.generate()` to accept a languages set:

```python
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mahabharatha.devcontainer_features import (
    DEVCONTAINER_FEATURES,
    CUSTOM_INSTALL_COMMANDS,
    BASE_IMAGE,
    COMMON_FEATURES,
    get_features_for_languages,
    get_custom_install_commands,
)


class DevcontainerGenerator:
    """Generate devcontainer configuration for MAHABHARATHA workers."""

    def __init__(self, project_path: Path, config: DevcontainerConfig | None = None):
        """Initialize generator.

        Args:
            project_path: Path to project root
            config: Devcontainer configuration
        """
        self.project_path = project_path
        self.config = config or DevcontainerConfig()
        self.devcontainer_dir = project_path / ".devcontainer"

    def generate(
        self,
        language: str = "python",
        framework: str | None = None,
        languages: set[str] | None = None,
    ) -> Path:
        """Generate devcontainer files.

        Args:
            language: Primary project language (legacy, for single-lang)
            framework: Optional framework name
            languages: Set of languages for multi-language support (preferred)

        Returns:
            Path to generated .devcontainer directory
        """
        # Create directory
        self.devcontainer_dir.mkdir(parents=True, exist_ok=True)

        # Determine if multi-language
        if languages and len(languages) > 1:
            self._generate_multi_language(languages)
        else:
            # Single language - use existing logic or new features approach
            effective_lang = next(iter(languages)) if languages else language
            self._generate_dockerfile(effective_lang)
            self._generate_devcontainer_json(effective_lang, framework)
            self._generate_docker_compose()
            self._generate_post_create(effective_lang)

        return self.devcontainer_dir

    def _generate_multi_language(self, languages: set[str]) -> None:
        """Generate config for multi-language project using features.

        Args:
            languages: Set of detected languages
        """
        # Get features
        features = get_features_for_languages(languages)

        # Get custom install commands
        custom_commands = get_custom_install_commands(languages)

        # Build devcontainer.json
        config = {
            "name": self.config.name,
            "image": BASE_IMAGE,
            "features": features,
            "workspaceFolder": "/workspace",
            "workspaceMount": "source=${localWorkspaceFolder},target=/workspace,type=bind",
            "remoteUser": "root",
            "customizations": {
                "vscode": {
                    "extensions": list(self.config.extensions) + ["anthropic.claude-code"],
                }
            },
            "forwardPorts": [],
            "runArgs": ["--network=mahabharatha-internal"],
        }

        # Add postCreateCommand if needed
        post_commands = list(custom_commands)
        post_commands.extend(self.config.post_create_commands)
        post_commands.append("echo 'MAHABHARATHA worker ready'")

        if post_commands:
            config["postCreateCommand"] = " && ".join(post_commands)

        # Write devcontainer.json
        devcontainer_json_path = self.devcontainer_dir / "devcontainer.json"
        devcontainer_json_path.write_text(json.dumps(config, indent=2))

        # Generate docker-compose for resource limits
        self._generate_docker_compose()

        # Generate post-create script
        self._generate_multi_lang_post_create(languages)

    def _generate_multi_lang_post_create(self, languages: set[str]) -> None:
        """Generate post-create script for multi-language setup.

        Args:
            languages: Set of detected languages
        """
        install_commands = []

        for lang in sorted(languages):
            if lang == "python":
                install_commands.append(
                    'if [ -f requirements.txt ]; then pip install -r requirements.txt; fi'
                )
                install_commands.append(
                    'if [ -f pyproject.toml ]; then pip install -e .; fi'
                )
            elif lang in ("javascript", "typescript"):
                install_commands.append('if [ -f package.json ]; then npm install; fi')
            elif lang == "go":
                install_commands.append('if [ -f go.mod ]; then go mod download; fi')
            elif lang == "rust":
                install_commands.append('if [ -f Cargo.toml ]; then cargo fetch; fi')

        # Add custom commands
        install_commands.extend(self.config.post_create_commands)

        content = POST_CREATE_TEMPLATE.format(
            install_commands="\n".join(install_commands) or "echo 'No dependencies to install'"
        )

        post_create_path = self.devcontainer_dir / "post-create.sh"
        post_create_path.write_text(content)
        post_create_path.chmod(0o755)

    # ... keep existing methods: _generate_dockerfile, _generate_devcontainer_json, etc.
```

## Verification

```bash
python -c "
import sys
sys.path.insert(0, '.')

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

spec = spec_from_file_location('devcontainer', '.mahabharatha/devcontainer.py')
module = module_from_spec(spec)
spec.loader.exec_module(module)

# Test multi-language generation
from tempfile import TemporaryDirectory
with TemporaryDirectory() as tmpdir:
    gen = module.DevcontainerGenerator(Path(tmpdir))
    result = gen.generate(languages={'python', 'go'})
    config_file = result / 'devcontainer.json'
    print(f'Config created: {config_file.exists()}')

    import json
    config = json.loads(config_file.read_text())
    print(f'Features count: {len(config.get(\"features\", {}))}')
    print(f'Has python feature: {\"python\" in str(config)}')
"
```

## Acceptance Criteria

- [ ] DevcontainerGenerator.generate() accepts optional `languages` set
- [ ] Multi-language (len > 1) uses features approach
- [ ] Single language falls back to existing behavior
- [ ] _generate_multi_language() creates proper features config
- [ ] Post-create script installs deps for all languages
- [ ] Import from mahabharatha.devcontainer_features works
- [ ] No syntax errors in the module
