# DC-004: Update create_devcontainer() to Use Dynamic Generator

**Level**: 3 | **Critical Path**: Yes ⭐ | **Estimate**: 25 min
**Dependencies**: DC-001, DC-003

## Objective

Modify `create_devcontainer()` in `mahabharatha/commands/init.py` to use `DynamicDevcontainerGenerator` with the detected `ProjectStack` instead of static single-language configuration.

## Files Owned

- `mahabharatha/commands/init.py` (modify)

## Files to Read

- `mahabharatha/devcontainer_features.py` (DynamicDevcontainerGenerator)

## Implementation

Replace the existing `create_devcontainer()` function:

```python
from mahabharatha.devcontainer_features import DynamicDevcontainerGenerator
from mahabharatha.security_rules import ProjectStack


def create_devcontainer(stack: ProjectStack, security: str) -> None:
    """Create devcontainer configuration.

    Args:
        stack: Detected project stack
        security: Security level
    """
    # Use dynamic generator for multi-language support
    generator = DynamicDevcontainerGenerator(stack, name="MAHABHARATHA Worker")
    config = generator.generate_config()

    # Add security settings for strict mode
    if security == "strict":
        config["runArgs"] = [
            "--read-only",
            "--security-opt=no-new-privileges:true",
        ]

    # Create directory and write config
    devcontainer_dir = Path(".devcontainer")
    devcontainer_dir.mkdir(exist_ok=True)

    devcontainer_path = devcontainer_dir / "devcontainer.json"
    with open(devcontainer_path, "w") as f:
        json.dump(config, f, indent=2)

    console.print(f"  [green]✓[/green] Created {devcontainer_path}")

    # Show detected languages in devcontainer
    if stack.languages:
        langs = ", ".join(sorted(stack.languages))
        console.print(f"    Languages: [cyan]{langs}[/cyan]")
```

Also update the call site in `init()`:

```python
# Old
create_devcontainer(project_type, security)

# New
create_devcontainer(stack, security)
```

And update `create_config()` signature and body:

```python
def create_config(workers: int, security: str, stack: ProjectStack) -> dict:
    """Create configuration dictionary.

    Args:
        workers: Default worker count
        security: Security level
        stack: Detected project stack

    Returns:
        Configuration dict
    """
    # For backwards compatibility, use primary language as project_type
    primary_type = next(iter(sorted(stack.languages)), None) if stack.languages else None

    # ... rest of existing logic ...

    return {
        "version": "1.0",
        "project_type": primary_type or "unknown",
        "detected_stack": stack.to_dict(),  # New: full stack info
        "workers": { ... },
        "security": security_settings.get(security, security_settings["standard"]),
        "quality_gates": get_quality_gates(primary_type),
        "mcp_servers": get_default_mcp_servers(),
    }
```

## Verification

```bash
# Test multi-language detection and devcontainer creation
cd /tmp && rm -rf test-dc-multi && mkdir test-dc-multi && cd test-dc-multi

# Create files for Python + Node + Go
touch requirements.txt package.json go.mod

# Run init
mahabharatha init --no-security-rules

# Check devcontainer has multiple features
python -c "
import json
with open('.devcontainer/devcontainer.json') as f:
    config = json.load(f)
features = config.get('features', {})
print('Features:')
for url in features:
    print(f'  - {url}')
has_python = 'python' in str(features)
has_node = 'node' in str(features)
has_go = 'go' in str(features)
print(f'Python: {has_python}, Node: {has_node}, Go: {has_go}')
assert has_python and has_node and has_go, 'Missing expected features'
print('OK: All expected features present')
"
```

## Acceptance Criteria

- [ ] create_devcontainer() accepts ProjectStack instead of str
- [ ] Uses DynamicDevcontainerGenerator for config generation
- [ ] Multi-language projects get multi-feature devcontainer.json
- [ ] Single-language projects still work correctly
- [ ] Security level still applies runArgs for strict mode
- [ ] create_config() stores full stack info in detected_stack
- [ ] Backwards compatible: project_type still set (primary language)
- [ ] No ruff errors: `ruff check mahabharatha/commands/init.py`
