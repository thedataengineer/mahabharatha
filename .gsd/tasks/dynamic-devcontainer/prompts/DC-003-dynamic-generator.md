# DC-003: Create DynamicDevcontainerGenerator

**Level**: 2 | **Critical Path**: Yes ⭐ | **Estimate**: 30 min
**Dependencies**: DC-002

## Objective

Add `DynamicDevcontainerGenerator` class to `mahabharatha/devcontainer_features.py` that generates devcontainer.json configs with multi-language features based on `ProjectStack`.

## Files Owned

- `mahabharatha/devcontainer_features.py` (modify - add class)

## Files to Read

- `mahabharatha/security_rules.py` (reference ProjectStack)

## Implementation

Add to `mahabharatha/devcontainer_features.py`:

```python
from dataclasses import dataclass
from pathlib import Path
import json

from mahabharatha.security_rules import ProjectStack


@dataclass
class DevcontainerSpec:
    """Generated devcontainer specification."""

    name: str
    image: str
    features: dict[str, dict[str, Any]]
    post_create_commands: list[str]
    workspace_folder: str = "/workspace"

    def to_dict(self) -> dict[str, Any]:
        """Convert to devcontainer.json dict."""
        config = {
            "name": self.name,
            "image": self.image,
            "features": self.features,
            "workspaceFolder": self.workspace_folder,
            "workspaceMount": "source=${localWorkspaceFolder},target=/workspace,type=bind",
            "customizations": {
                "vscode": {
                    "extensions": ["anthropic.claude-code"]
                }
            },
        }

        if self.post_create_commands:
            # Join multiple commands with &&
            config["postCreateCommand"] = " && ".join(self.post_create_commands)

        return config

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class DynamicDevcontainerGenerator:
    """Generate devcontainer configs for multi-language projects."""

    def __init__(self, stack: ProjectStack, name: str = "mahabharatha-worker"):
        """Initialize generator.

        Args:
            stack: Detected project stack
            name: Container name
        """
        self.stack = stack
        self.name = name

    def generate_config(self) -> dict[str, Any]:
        """Generate devcontainer.json configuration.

        Returns:
            Configuration dict ready for JSON serialization
        """
        spec = self.generate_spec()
        return spec.to_dict()

    def generate_spec(self) -> DevcontainerSpec:
        """Generate devcontainer specification.

        Returns:
            DevcontainerSpec with all configuration
        """
        # Get features for detected languages
        features = get_features_for_languages(self.stack.languages)

        # Get custom install commands for unsupported languages
        custom_commands = get_custom_install_commands(self.stack.languages)

        # Add framework-specific post-create commands
        post_commands = list(custom_commands)
        post_commands.append("echo 'MAHABHARATHA worker ready'")

        # Determine image
        if len(self.stack.languages) > 1:
            # Multi-language: use base image with features
            image = BASE_IMAGE
        elif self.stack.languages:
            # Single language: could use language-specific image
            # but features approach is more consistent
            image = BASE_IMAGE
        else:
            # No languages detected
            image = BASE_IMAGE

        return DevcontainerSpec(
            name=self.name,
            image=image,
            features=features,
            post_create_commands=post_commands,
        )

    def write_to_file(self, output_dir: Path) -> Path:
        """Write devcontainer.json to directory.

        Args:
            output_dir: Directory for .devcontainer (parent of devcontainer.json)

        Returns:
            Path to created devcontainer.json
        """
        devcontainer_dir = output_dir / ".devcontainer"
        devcontainer_dir.mkdir(parents=True, exist_ok=True)

        config_path = devcontainer_dir / "devcontainer.json"
        config_path.write_text(self.generate_spec().to_json())

        return config_path

    @classmethod
    def from_languages(cls, languages: set[str], name: str = "mahabharatha-worker") -> "DynamicDevcontainerGenerator":
        """Create generator from language set.

        Args:
            languages: Set of language names
            name: Container name

        Returns:
            DynamicDevcontainerGenerator instance
        """
        stack = ProjectStack(languages=languages)
        return cls(stack, name)
```

## Verification

```bash
python -c "
from mahabharatha.devcontainer_features import DynamicDevcontainerGenerator
from mahabharatha.security_rules import ProjectStack

# Test multi-language
stack = ProjectStack(languages={'python', 'go', 'r'})
gen = DynamicDevcontainerGenerator(stack)
config = gen.generate_config()

print('Features:', list(config.get('features', {}).keys()))
print('Has postCreateCommand:', 'postCreateCommand' in config)
print('Image:', config.get('image'))
"
```

Expected output:
```
Features: ['ghcr.io/devcontainers/features/git:1', 'ghcr.io/devcontainers/features/github-cli:1', 'ghcr.io/devcontainers/features/python:1', 'ghcr.io/devcontainers/features/go:1']
Has postCreateCommand: True
Image: mcr.microsoft.com/devcontainers/base:ubuntu
```

## Acceptance Criteria

- [ ] DynamicDevcontainerGenerator takes ProjectStack
- [ ] generate_config() returns valid devcontainer.json dict
- [ ] Features include all detected languages with official support
- [ ] postCreateCommand includes custom installs for R, Julia, C++
- [ ] write_to_file() creates .devcontainer/devcontainer.json
- [ ] from_languages() factory method works
- [ ] No ruff errors
