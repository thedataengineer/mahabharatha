# DC-002: Create devcontainer_features.py with Feature Mapping

**Level**: 1 | **Critical Path**: Yes ⭐ | **Estimate**: 15 min

## Objective

Create new module `mahabharatha/devcontainer_features.py` with mappings from detected languages to devcontainer feature URLs.

## Files Owned

- `mahabharatha/devcontainer_features.py` (create)

## Implementation

Create the module with these constants:

```python
"""Devcontainer feature mappings for multi-language support."""

from typing import Any

# Mapping: language -> (feature_url, default_options)
DEVCONTAINER_FEATURES: dict[str, tuple[str, dict[str, Any]] | None] = {
    "python": ("ghcr.io/devcontainers/features/python:1", {"version": "3.12"}),
    "javascript": ("ghcr.io/devcontainers/features/node:1", {"version": "20"}),
    "typescript": ("ghcr.io/devcontainers/features/node:1", {"version": "20"}),
    "go": ("ghcr.io/devcontainers/features/go:1", {"version": "1.22"}),
    "rust": ("ghcr.io/devcontainers/features/rust:1", {}),
    "java": ("ghcr.io/devcontainers/features/java:1", {"version": "21"}),
    "ruby": ("ghcr.io/devcontainers/features/ruby:1", {}),
    "csharp": ("ghcr.io/devcontainers/features/dotnet:1", {"version": "8.0"}),
    # Languages requiring custom install (None = use postCreateCommand)
    "r": None,
    "julia": None,
    "cpp": None,
    "sql": None,  # No runtime needed
}

# Custom install commands for languages without official features
CUSTOM_INSTALL_COMMANDS: dict[str, str] = {
    "r": "apt-get update && apt-get install -y r-base r-base-dev",
    "julia": "curl -fsSL https://install.julialang.org | sh -s -- -y",
    "cpp": "apt-get update && apt-get install -y build-essential cmake gdb",
}

# Base image for multi-language containers
BASE_IMAGE = "mcr.microsoft.com/devcontainers/base:ubuntu"

# Common features always included
COMMON_FEATURES: dict[str, dict[str, Any]] = {
    "ghcr.io/devcontainers/features/git:1": {},
    "ghcr.io/devcontainers/features/github-cli:1": {},
}


def get_features_for_languages(languages: set[str]) -> dict[str, dict[str, Any]]:
    """Get devcontainer features for a set of languages.

    Args:
        languages: Set of detected language names

    Returns:
        Dict of feature URLs to options
    """
    features = dict(COMMON_FEATURES)

    for lang in languages:
        feature_info = DEVCONTAINER_FEATURES.get(lang)
        if feature_info is not None:
            url, options = feature_info
            # Avoid duplicates (e.g., javascript and typescript both use node)
            if url not in features:
                features[url] = options

    return features


def get_custom_install_commands(languages: set[str]) -> list[str]:
    """Get custom install commands for languages without features.

    Args:
        languages: Set of detected language names

    Returns:
        List of shell commands to run in postCreateCommand
    """
    commands = []
    for lang in languages:
        if lang in CUSTOM_INSTALL_COMMANDS:
            commands.append(CUSTOM_INSTALL_COMMANDS[lang])
    return commands
```

## Verification

```bash
python -c "
from mahabharatha.devcontainer_features import (
    DEVCONTAINER_FEATURES,
    CUSTOM_INSTALL_COMMANDS,
    get_features_for_languages,
    get_custom_install_commands
)
print(f'Features: {len(DEVCONTAINER_FEATURES)}')
print(f'Custom: {len(CUSTOM_INSTALL_COMMANDS)}')
print(f'Python+Go: {get_features_for_languages({\"python\", \"go\"})}')
"
```

## Acceptance Criteria

- [ ] Module imports without error
- [ ] DEVCONTAINER_FEATURES has 8+ language mappings
- [ ] CUSTOM_INSTALL_COMMANDS handles R, Julia, C++
- [ ] get_features_for_languages() returns correct dict
- [ ] get_custom_install_commands() returns install scripts
- [ ] No ruff errors
