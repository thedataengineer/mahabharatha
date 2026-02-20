# DC-011: Update Skill Files with Container Mode Docs

**Level**: 5 | **Critical Path**: No | **Estimate**: 20 min
**Dependencies**: DC-010

## Objective

Update `mahabharatha:init.md` and `mahabharatha:kurukshetra.md` skill files to document:
- Multi-language project detection
- Container mode options
- Examples of container-based execution

## Files Owned

- `.claude/commands/mahabharatha:init.md` (modify)
- `.claude/commands/mahabharatha:kurukshetra.md` (modify)

## Implementation

### 1. Update `.claude/commands/mahabharatha:init.md`

Add section about multi-language detection:

```markdown
## Multi-Language Detection

MAHABHARATHA automatically detects all languages in your project:

- **Python**: pyproject.toml, requirements.txt, setup.py, *.py
- **JavaScript/TypeScript**: package.json, tsconfig.json, *.js, *.ts
- **Go**: go.mod, *.go
- **Rust**: Cargo.toml, *.rs
- **Java**: pom.xml, build.gradle, *.java
- **Ruby**: Gemfile, *.rb
- **C++**: CMakeLists.txt, *.cpp, *.hpp
- **R**: *.R, *.r
- **Julia**: *.jl

### Multi-Language Devcontainer

For projects with multiple languages, MAHABHARATHA generates a devcontainer with multiple runtime features:

```json
{
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
  "features": {
    "ghcr.io/devcontainers/features/python:1": {"version": "3.12"},
    "ghcr.io/devcontainers/features/node:1": {"version": "20"},
    "ghcr.io/devcontainers/features/go:1": {"version": "1.22"}
  }
}
```

### Building Container Image

To build the devcontainer image during init:

```bash
mahabharatha init --with-containers
```

This enables container mode for `mahabharatha kurukshetra`.
```

### 2. Update `.claude/commands/mahabharatha:kurukshetra.md`

Add section about execution modes:

```markdown
## Execution Modes

MAHABHARATHA supports three execution modes:

### Subprocess Mode (Default)

Workers run as local Python subprocesses:

```bash
mahabharatha kurukshetra --mode subprocess --workers 5
```

- No Docker required
- Uses local environment
- Good for development

### Container Mode

Workers run in isolated Docker containers:

```bash
mahabharatha kurukshetra --mode container --workers 5
```

Requirements:
- Docker installed and running
- Devcontainer image built (`mahabharatha init --with-containers`)
- ANTHROPIC_API_KEY in environment

Benefits:
- Isolated environments
- Consistent dependencies
- Resource limits per worker

### Auto Mode (Default)

Automatically selects the best mode:

```bash
mahabharatha kurukshetra --mode auto --workers 5
# or simply:
mahabharatha kurukshetra --workers 5
```

Auto-detection logic:
1. If `.devcontainer/devcontainer.json` exists AND
2. Docker is available AND
3. `mahabharatha-worker` image is built
→ Uses container mode

Otherwise → Uses subprocess mode

## Examples

```bash
# Quick local execution
mahabharatha kurukshetra --workers 3

# Force container mode
mahabharatha kurukshetra --mode container --workers 5

# Dry run to check mode selection
mahabharatha kurukshetra --dry-run
# Shows: "Auto-detected mode: container" or "subprocess"

# Build containers first, then run
mahabharatha init --with-containers
mahabharatha kurukshetra --mode container --workers 5
```
```

## Verification

```bash
# Check mahabharatha:init.md has multi-language docs
grep -l 'Multi-Language' .claude/commands/mahabharatha:init.md

# Check mahabharatha:kurukshetra.md has container mode docs
grep -l 'Container Mode' .claude/commands/mahabharatha:kurukshetra.md
grep -l '\-\-mode' .claude/commands/mahabharatha:kurukshetra.md

# Count occurrences
echo "Container mentions:"
grep -c 'container' .claude/commands/mahabharatha:*.md
```

## Acceptance Criteria

- [ ] mahabharatha:init.md documents multi-language detection
- [ ] mahabharatha:init.md shows example multi-feature devcontainer.json
- [ ] mahabharatha:init.md documents --with-containers flag
- [ ] mahabharatha:kurukshetra.md documents subprocess, container, auto modes
- [ ] mahabharatha:kurukshetra.md shows --mode flag usage
- [ ] mahabharatha:kurukshetra.md explains auto-detection logic
- [ ] Both files have usage examples
- [ ] No broken markdown formatting
