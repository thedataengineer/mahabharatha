# ZERG

**Zero-Effort Rapid Growth** - Parallel Claude Code execution system for spec-driven development.

> "Zerg rush your codebase." - Overwhelm features with coordinated worker instances.

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Install from Source](#install-from-source)
  - [Verify Installation](#verify-installation)
- [Quick Start](#quick-start)
  - [Inception Mode (New Project)](#inception-mode-new-project)
  - [Discovery Mode (Existing Project)](#discovery-mode-existing-project)
- [Core Concepts](#core-concepts)
- [Complete Command Reference](#complete-command-reference)
  - [Workflow Commands](#workflow-commands)
    - [/zerg:init](#zerginit)
    - [/zerg:plan](#zergplan)
    - [/zerg:design](#zergdesign)
    - [/zerg:rush](#zergrush)
  - [Monitoring Commands](#monitoring-commands)
    - [/zerg:status](#zergstatus)
    - [/zerg:logs](#zerglogs)
    - [/zerg:stop](#zergstop)
  - [Task Management Commands](#task-management-commands)
    - [/zerg:retry](#zergretry)
    - [/zerg:merge](#zergmerge)
    - [/zerg:cleanup](#zergcleanup)
  - [Quality Commands](#quality-commands)
    - [/zerg:test](#zergtest)
    - [/zerg:build](#zergbuild)
    - [/zerg:analyze](#zerganalyze)
    - [/zerg:review](#zergreview)
  - [Development Commands](#development-commands)
    - [/zerg:refactor](#zergrefactor)
    - [/zerg:troubleshoot](#zergtroubleshoot)
    - [/zerg:git](#zerggit)
  - [Infrastructure Commands](#infrastructure-commands)
    - [/zerg:security](#zergsecurity)
    - [/zerg:worker](#zergworker)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Tutorial](#tutorial)

---

## Overview

ZERG combines three powerful approaches to accelerate development:

1. **GSD Methodology**: Spec-first development with fresh Claude Code instances per task
2. **Claude Code Skills**: `/zerg:*` slash commands invoke CLI commands with structured prompts
3. **Devcontainers**: Isolated parallel execution environments with Docker

**How it works:**
1. You describe what you want to build
2. ZERG captures requirements and creates a technical design
3. Work is broken into atomic tasks with exclusive file ownership
4. Multiple Claude Code workers execute tasks in parallel
5. Quality gates validate each level before merging

---

## Installation

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Runtime environment |
| Git | 2.x+ | Version control and worktrees |
| Docker | 20.x+ | Container mode (optional) |
| Claude Code CLI | Latest | AI-powered development |
| `ANTHROPIC_API_KEY` | - | API authentication |

### Install from Source

```bash
# Clone the repository
git clone https://github.com/rocklambros/zerg.git
cd zerg

# Install in development mode
pip install -e .

# Or install with all dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Check version
zerg --version

# View available commands
zerg --help

# Verify environment
echo $ANTHROPIC_API_KEY  # Should show your API key
```

**Expected output:**
```
Usage: zerg [OPTIONS] COMMAND [ARGS]...

  ZERG - Parallel Claude Code execution system.

Options:
  --version      Show the version and exit.
  -v, --verbose  Enable verbose output
  -q, --quiet    Suppress non-essential output
  --help         Show this message and exit.

Commands:
  analyze          Static analysis and quality metrics
  build            Build with error recovery
  cleanup          Remove ZERG artifacts
  design           Generate architecture and task graph
  git              Git operations and workflow
  init             Initialize ZERG for a project
  logs             Stream worker logs
  merge            Merge level branches
  plan             Capture feature requirements
  refactor         Automated code improvement
  retry            Retry failed tasks
  review           Two-stage code review
  rush             Launch parallel workers
  security-rules   Security rules management
  status           Show execution status
  stop             Stop workers
  test             Run tests with coverage
  troubleshoot     Debug with root cause analysis
```

---

## Quick Start

ZERG operates in two modes depending on your starting point:

### Inception Mode (New Project)

Start a brand-new project from scratch with guided setup:

```bash
# Create empty directory
mkdir my-new-api && cd my-new-api

# Run ZERG init - detects empty directory, starts Inception Mode
zerg init

# Follow the interactive prompts:
#   - Project name and description
#   - Target platform (api, cli, web, library)
#   - Technology stack recommendation
#   - Project scaffolding
```

**What Inception Mode does:**
1. **Gathers Requirements** - Interactive prompts capture project goals
2. **Recommends Technology** - Suggests language, framework, and tools
3. **Scaffolds Project** - Generates complete project structure
4. **Initializes Git** - Creates initial commit with `.gitignore`

### Discovery Mode (Existing Project)

Add ZERG to an existing codebase:

```bash
# Navigate to your existing project
cd your-existing-project

# Initialize ZERG - detects existing project, runs Discovery Mode
zerg init --security standard

# ZERG analyzes your project and configures itself
```

### Complete Workflow Example

```bash
# 1. Initialize ZERG (one-time setup)
zerg init --workers 5 --security standard

# 2. Plan a feature (captures requirements)
zerg plan user-authentication --socratic

# 3. Review and approve requirements
# Edit .gsd/specs/user-authentication/requirements.md if needed

# 4. Design the implementation (creates task graph)
zerg design --feature user-authentication

# 5. Review the design
# Check .gsd/specs/user-authentication/design.md
# Check .gsd/specs/user-authentication/task-graph.json

# 6. Launch parallel workers
zerg rush --workers 5

# 7. Monitor progress
zerg status --watch

# 8. View logs if needed
zerg logs --follow

# 9. Retry any failed tasks
zerg retry --all-failed

# 10. Clean up when done
zerg cleanup --feature user-authentication
```

---

## Core Concepts

### Levels

Tasks are organized into dependency levels:

| Level | Name | Purpose | Dependencies |
|-------|------|---------|--------------|
| 1 | Foundation | Types, schemas, configs | None |
| 2 | Core | Business logic, services | Level 1 |
| 3 | Integration | APIs, routes, handlers | Level 2 |
| 4 | Testing | Tests, validation | Level 3 |
| 5 | Quality | Docs, polish, cleanup | Level 4 |

All tasks at a level run in parallel. Level N+1 starts only after Level N completes and passes quality gates.

### File Ownership

Each task owns specific files exclusively:
- **Create**: Only one task can create a file
- **Modify**: Only one task can modify a file per level
- **Read**: Multiple tasks can read the same file

This prevents merge conflicts entirely.

### Workers

Workers are isolated Claude Code instances:
- Each worker has its own git worktree
- Workers claim and execute tasks
- Workers commit changes to their branches
- Orchestrator merges branches after each level

### Spec Files

All coordination flows through spec files in `.gsd/`:

| File | Purpose |
|------|---------|
| `PROJECT.md` | Project vision and constraints |
| `INFRASTRUCTURE.md` | Technical stack and services |
| `specs/{feature}/requirements.md` | Feature requirements |
| `specs/{feature}/design.md` | Architecture and design |
| `specs/{feature}/task-graph.json` | Task definitions |
| `STATE.md` | Execution progress |

---

## Complete Command Reference

### Workflow Commands

---

#### /zerg:init

**Initialize ZERG for a project.**

Creates `.zerg/` configuration, `.devcontainer/` setup, and integrates security rules.

**Usage:**
```bash
zerg init [OPTIONS]
```

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--detect/--no-detect` | flag | `--detect` | Auto-detect project type from files |
| `--workers`, `-w` | integer | `5` | Default number of workers (1-10) |
| `--security` | choice | `standard` | Security level: `minimal`, `standard`, `strict` |
| `--with-security-rules/--no-security-rules` | flag | `--with-security-rules` | Fetch secure coding rules from TikiTribe repo |
| `--with-containers/--no-containers` | flag | `--no-containers` | Build devcontainer image after init |
| `--force` | flag | `false` | Overwrite existing configuration |

**Security Levels:**

| Level | Network Isolation | Filesystem Sandbox | Secrets Scanning | Additional |
|-------|-------------------|--------------------|--------------------|------------|
| `minimal` | No | No | No | - |
| `standard` | Yes | Yes | Yes | - |
| `strict` | Yes | Yes | Yes | Read-only root, no new privileges |

**Examples:**

```bash
# Basic initialization with defaults
zerg init

# Initialize with 3 workers and strict security
zerg init --workers 3 --security strict

# Skip auto-detection, force reinitialize
zerg init --no-detect --force

# Build devcontainer image immediately
zerg init --with-containers

# Skip security rules (faster init)
zerg init --no-security-rules
```

**Output:**
- `.zerg/config.yaml` - ZERG configuration
- `.zerg/state/` - Execution state directory
- `.zerg/logs/` - Worker logs directory
- `.zerg/worktrees/` - Git worktrees directory
- `.devcontainer/devcontainer.json` - Container configuration
- `.devcontainer/Dockerfile` - Multi-language runtime
- `.gsd/PROJECT.md` - Project documentation
- `.gsd/INFRASTRUCTURE.md` - Infrastructure requirements
- `.claude/security-rules/` - Secure coding rules (if enabled)

---

#### /zerg:plan

**Capture comprehensive feature requirements.**

Creates a detailed requirements document with user stories, acceptance criteria, and verification commands.

**Usage:**
```bash
zerg plan [FEATURE] [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `FEATURE` | Yes* | Feature name (kebab-case). *Not required with `--from-issue` |

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--template`, `-t` | choice | `default` | Template style: `default`, `minimal`, `detailed` |
| `--interactive/--no-interactive` | flag | `--interactive` | Enable/disable interactive prompts |
| `--from-issue` | string | - | Import requirements from GitHub issue URL |
| `--socratic`, `-s` | flag | `false` | Use structured 3-round Socratic discovery |
| `--rounds` | integer | `3` | Number of Socratic rounds (1-5) |
| `--verbose`, `-v` | flag | `false` | Verbose output |

**Templates:**

| Template | Description | Best For |
|----------|-------------|----------|
| `default` | Balanced detail level | Most features |
| `minimal` | Essential fields only | Quick prototypes |
| `detailed` | Comprehensive sections | Complex features |

**Socratic Mode:**

When `--socratic` is enabled, ZERG guides you through structured discovery:

1. **Round 1 - Problem Space** (5 questions)
   - What problem does this solve?
   - Who are the users?
   - What's the impact of not solving this?

2. **Round 2 - Solution Space** (5 questions)
   - What are the boundaries?
   - What's explicitly out of scope?
   - What are the constraints?

3. **Round 3 - Implementation Space** (5 questions)
   - What are the acceptance criteria?
   - How will we verify success?
   - What are the dependencies?

**Examples:**

```bash
# Interactive planning with default template
zerg plan user-authentication

# Socratic discovery mode (recommended for complex features)
zerg plan user-authentication --socratic

# Extended Socratic with 5 rounds
zerg plan user-authentication --socratic --rounds 5

# Import from GitHub issue
zerg plan --from-issue https://github.com/org/repo/issues/123

# Non-interactive with minimal template
zerg plan api-v2 --template minimal --no-interactive

# Detailed template with verbose output
zerg plan payment-integration --template detailed --verbose
```

**Output:**
- `.gsd/specs/{feature}/requirements.md` - Requirements document
- `.gsd/.current-feature` - Active feature marker
- `.gsd/specs/{feature}/.started` - Creation timestamp

---

#### /zerg:design

**Generate technical architecture and task graph.**

Creates detailed architecture documentation and breaks work into parallelizable tasks with exclusive file ownership.

**Usage:**
```bash
zerg design [OPTIONS]
```

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--feature`, `-f` | string | auto-detect | Feature name (uses current if not specified) |
| `--max-task-minutes` | integer | `30` | Maximum duration per task in minutes |
| `--min-task-minutes` | integer | `5` | Minimum duration per task in minutes |
| `--validate-only` | flag | `false` | Validate existing task graph without regenerating |
| `--verbose`, `-v` | flag | `false` | Verbose output |

**Prerequisites:**
- `.gsd/specs/{feature}/requirements.md` must exist
- Requirements should be approved (status: APPROVED)

**Task Graph Schema (v2.0):**

```json
{
  "feature": "user-auth",
  "version": "2.0",
  "generated": "2026-01-26T10:30:00Z",
  "total_tasks": 15,
  "estimated_duration_minutes": 120,
  "max_parallelization": 5,
  "tasks": [
    {
      "id": "USER-AUTH-L1-001",
      "title": "Create user types and schemas",
      "description": "Define User, Session, Token types",
      "phase": "foundation",
      "level": 1,
      "dependencies": [],
      "files": {
        "create": ["src/types/user.py"],
        "modify": [],
        "read": ["src/types/__init__.py"]
      },
      "acceptance_criteria": [
        "User type has id, email, password_hash fields",
        "Session type has user_id, token, expires_at fields"
      ],
      "verification": {
        "command": "python -c \"from src.types.user import User, Session\"",
        "timeout_seconds": 30
      },
      "estimate_minutes": 10
    }
  ]
}
```

**Examples:**

```bash
# Design current feature (auto-detected)
zerg design

# Design specific feature
zerg design --feature user-authentication

# Validate existing task graph without changes
zerg design --validate-only

# Custom task duration bounds
zerg design --max-task-minutes 45 --min-task-minutes 10

# Verbose output for debugging
zerg design --feature api-v2 --verbose
```

**Output:**
- `.gsd/specs/{feature}/design.md` - Architecture document
- `.gsd/specs/{feature}/task-graph.json` - Task definitions

---

#### /zerg:rush

**Launch parallel worker execution.**

Spawns multiple Claude Code workers, assigns tasks, and orchestrates parallel execution across dependency levels.

**Usage:**
```bash
zerg rush [OPTIONS]
```

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--workers`, `-w` | integer | `5` | Number of workers to launch (1-10) |
| `--feature`, `-f` | string | auto-detect | Feature name |
| `--level`, `-l` | integer | `1` | Start from specific level |
| `--task-graph`, `-g` | path | auto-detect | Path to task-graph.json |
| `--mode`, `-m` | choice | `auto` | Worker mode: `subprocess`, `container`, `auto` |
| `--dry-run` | flag | `false` | Show execution plan without starting |
| `--resume` | flag | `false` | Continue from previous run |
| `--timeout` | integer | `3600` | Maximum execution time in seconds |
| `--verbose`, `-v` | flag | `false` | Verbose output |

**Execution Modes:**

| Mode | Description | Requirements |
|------|-------------|--------------|
| `auto` | Auto-detect best mode | Prefers container if available |
| `subprocess` | Local Python processes | No Docker required |
| `container` | Isolated Docker containers | Docker + built image |

**Auto-Detection Logic:**
1. If `.devcontainer/devcontainer.json` exists AND worker image is built → **container mode**
2. Otherwise → **subprocess mode**

**Examples:**

```bash
# Launch 5 workers (default)
zerg rush

# Launch with specific worker count
zerg rush --workers 3

# Preview execution plan without starting
zerg rush --dry-run

# Resume interrupted execution
zerg rush --resume

# Resume with different worker count
zerg rush --resume --workers 3

# Start from level 2 (skip level 1)
zerg rush --level 2

# Force container mode
zerg rush --mode container --workers 5

# Force subprocess mode (no Docker)
zerg rush --mode subprocess

# Extended timeout for large features
zerg rush --timeout 7200  # 2 hours

# Specific feature with verbose output
zerg rush --feature user-auth --verbose
```

**Output:**
- `.zerg/state/{feature}.json` - Execution state
- `.zerg/logs/worker-{id}.log` - Worker logs
- `.zerg/worktrees/{feature}-worker-N/` - Git worktrees
- `.gsd/specs/{feature}/worker-assignments.json` - Task assignments
- `.gsd/STATE.md` - Human-readable progress

---

### Monitoring Commands

---

#### /zerg:status

**Display current execution status and progress.**

Shows real-time progress across all workers and levels with optional continuous updates.

**Usage:**
```bash
zerg status [OPTIONS]
```

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--feature`, `-f` | string | auto-detect | Feature to show status for |
| `--watch`, `-w` | flag | `false` | Continuous update mode |
| `--interval` | integer | `5` | Watch refresh interval in seconds |
| `--level`, `-l` | integer | - | Filter to specific level |
| `--json` | flag | `false` | Output as JSON for scripting |

**Status Icons:**

| Icon | Status | Meaning |
|------|--------|---------|
| `[green]` | running | Worker actively executing task |
| `[yellow]` | idle | Worker waiting for dependencies |
| `[blue]` | verifying | Running verification command |
| `[dim]` | stopped | Gracefully stopped |
| `[red]` | crashed | Exited unexpectedly |
| `[orange]` | checkpoint | Context limit reached |

**Examples:**

```bash
# Show current status
zerg status

# Watch with live updates (5 second refresh)
zerg status --watch

# Faster refresh rate
zerg status --watch --interval 2

# Filter to specific level
zerg status --level 2

# JSON output for scripting
zerg status --json

# Specific feature
zerg status --feature user-auth

# Combined options
zerg status --feature user-auth --watch --json
```

**Sample Output:**
```
═══════════════════════════════════════════════════════════════
Progress: ████████████░░░░░░░░ 60% (24/40 tasks)

Level 3 of 5 │ Workers: 5 active

┌────────┬────────────────────────────────┬──────────┬─────────┐
│ Worker │ Current Task                   │ Progress │ Status  │
├────────┼────────────────────────────────┼──────────┼─────────┤
│ W-0    │ TASK-015: Implement login API  │ ████░░   │ RUNNING │
│ W-1    │ TASK-016: Create user service  │ ██████   │ VERIFY  │
│ W-2    │ TASK-017: Add auth middleware  │ ██░░░░   │ RUNNING │
│ W-3    │ (waiting for dependency)       │ ░░░░░░   │ IDLE    │
│ W-4    │ TASK-018: Database migrations  │ ████░░   │ RUNNING │
└────────┴────────────────────────────────┴──────────┴─────────┘

Recent: ✓ TASK-014 (W-2) │ ✓ TASK-013 (W-1) │ ✓ TASK-012 (W-0)
═══════════════════════════════════════════════════════════════
```

---

#### /zerg:logs

**Stream and filter worker logs.**

Displays worker and orchestrator logs with filtering, streaming, and export options.

**Usage:**
```bash
zerg logs [WORKER_ID] [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `WORKER_ID` | No | Filter to specific worker (0-9) |

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--feature`, `-f` | string | auto-detect | Feature name |
| `--tail`, `-n` | integer | `100` | Number of lines to show |
| `--follow` | flag | `false` | Stream new logs continuously |
| `--level`, `-l` | choice | `info` | Log level filter: `debug`, `info`, `warn`, `error` |
| `--json` | flag | `false` | Raw JSON output |

**Log Levels:**

| Level | Color | Description |
|-------|-------|-------------|
| `debug` | dim | Detailed debugging information |
| `info` | blue | Normal operational messages |
| `warn` | yellow | Warning conditions |
| `error` | red | Error conditions |

**Examples:**

```bash
# Show recent logs from all workers
zerg logs

# Show logs from worker 1 only
zerg logs 1

# Stream logs in real-time
zerg logs --follow

# Debug level for detailed output
zerg logs --level debug

# Last 50 error messages only
zerg logs --tail 50 --level error

# JSON output for parsing
zerg logs --json

# Combined: stream worker 0 with debug level
zerg logs 0 --follow --level debug

# Specific feature logs
zerg logs --feature user-auth --tail 200
```

---

#### /zerg:stop

**Stop workers gracefully or forcefully.**

Terminates worker execution with optional graceful shutdown and checkpoint.

**Usage:**
```bash
zerg stop [OPTIONS]
```

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--feature`, `-f` | string | auto-detect | Feature to stop |
| `--worker`, `-w` | integer | - | Stop specific worker only (0-9) |
| `--force` | flag | `false` | Force immediate termination |
| `--timeout` | integer | `30` | Graceful shutdown timeout in seconds |

**Graceful vs Force:**

| Aspect | Graceful (default) | Force |
|--------|-------------------|-------|
| Checkpoint | Yes, WIP committed | No |
| State update | Yes | May be stale |
| Task status | PAUSED | FAILED |
| Uncommitted work | Saved | Lost |
| Container | Clean stop | Killed |

**Examples:**

```bash
# Graceful stop all workers (default)
zerg stop

# Stop specific feature
zerg stop --feature user-auth

# Force immediate stop (no checkpoint)
zerg stop --force

# Stop specific worker only
zerg stop --worker 3

# Force stop specific worker
zerg stop --worker 3 --force

# Extended graceful timeout
zerg stop --timeout 60
```

---

### Task Management Commands

---

#### /zerg:retry

**Retry failed or blocked tasks.**

Resets task state and re-queues for execution with retry limit enforcement.

**Usage:**
```bash
zerg retry [TASK_IDS...] [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `TASK_IDS` | No | Specific task IDs to retry |

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--feature`, `-f` | string | auto-detect | Feature name |
| `--level`, `-l` | integer | - | Retry all failed tasks in level |
| `--all-failed`, `-a` | flag | `false` | Retry all failed tasks |
| `--force` | flag | `false` | Bypass retry limit (default: 3) |
| `--timeout`, `-t` | integer | - | Override timeout in seconds |
| `--reset` | flag | `false` | Reset retry counters |
| `--dry-run` | flag | `false` | Show what would be retried |
| `--worker`, `-w` | integer | - | Assign to specific worker |
| `--verbose`, `-v` | flag | `false` | Verbose output |

**Examples:**

```bash
# Retry specific task
zerg retry TASK-001

# Retry multiple tasks
zerg retry TASK-001 TASK-002 TASK-003

# Retry all failed tasks
zerg retry --all-failed

# Retry all failed in level 2
zerg retry --level 2

# Force retry (bypass 3-attempt limit)
zerg retry TASK-001 --force

# Reset counters and retry
zerg retry --all-failed --reset

# Preview what would be retried
zerg retry --all-failed --dry-run

# Assign to specific worker
zerg retry TASK-001 --worker 2

# Override timeout
zerg retry TASK-001 --timeout 120
```

---

#### /zerg:merge

**Manage level merges and integrate worker branches.**

Merges worker branches after each level completes, runs quality gates, and rebases for next level.

**Usage:**
```bash
zerg merge [OPTIONS]
```

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--feature`, `-f` | string | auto-detect | Feature to merge |
| `--level`, `-l` | integer | current | Merge specific level |
| `--force` | flag | `false` | Force merge despite conflicts |
| `--abort` | flag | `false` | Abort in-progress merge |
| `--dry-run` | flag | `false` | Show merge plan only |
| `--skip-gates` | flag | `false` | Skip quality gate checks |
| `--no-rebase` | flag | `false` | Don't rebase worker branches |
| `--verbose`, `-v` | flag | `false` | Verbose output |

**Merge States:**

| State | Description |
|-------|-------------|
| `pending` | Level not yet complete |
| `waiting` | Waiting for workers to finish |
| `collecting` | Gathering worker branches |
| `merging` | Merge in progress |
| `validating` | Running quality gates |
| `rebasing` | Rebasing worker branches |
| `complete` | Merge successful |
| `conflict` | Manual intervention needed |
| `failed` | Merge or validation failed |

**Examples:**

```bash
# Merge current level
zerg merge

# Merge specific level
zerg merge --level 2

# Preview merge plan
zerg merge --dry-run

# Skip quality gates (use with caution)
zerg merge --skip-gates

# Force merge despite conflicts
zerg merge --force

# Abort failed merge
zerg merge --abort

# Don't rebase worker branches after
zerg merge --no-rebase

# Combined: verbose dry-run for level 3
zerg merge --level 3 --dry-run --verbose
```

---

#### /zerg:cleanup

**Remove ZERG artifacts and clean up resources.**

Removes worktrees, branches, containers, and logs while preserving merged code.

**Usage:**
```bash
zerg cleanup [OPTIONS]
```

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--feature`, `-f` | string | - | Feature to clean (required unless `--all`) |
| `--all` | flag | `false` | Clean all ZERG features |
| `--keep-logs` | flag | `false` | Preserve log files |
| `--keep-branches` | flag | `false` | Preserve git branches |
| `--dry-run` | flag | `false` | Preview cleanup plan |

**What Gets Cleaned:**

| Category | Removed | Preserved |
|----------|---------|-----------|
| Worktrees | `.zerg/worktrees/{feature}-*` | - |
| Branches | `zerg/{feature}/*` | main, develop |
| State | `.zerg/state/{feature}.json` | - |
| Logs | `.zerg/logs/worker-*.log` | With `--keep-logs` |
| Containers | `zerg-worker-*` | - |
| Specs | - | `.gsd/specs/{feature}/` |
| Source code | - | All merged changes |

**Examples:**

```bash
# Clean specific feature
zerg cleanup --feature user-auth

# Preview cleanup (no changes)
zerg cleanup --feature user-auth --dry-run

# Clean all features
zerg cleanup --all

# Keep logs for debugging
zerg cleanup --feature user-auth --keep-logs

# Keep branches for reference
zerg cleanup --feature user-auth --keep-branches

# Clean all but keep logs and branches
zerg cleanup --all --keep-logs --keep-branches
```

---

### Quality Commands

---

#### /zerg:test

**Execute tests with coverage analysis.**

Runs language-specific test frameworks with parallel execution and coverage reporting.

**Usage:**
```bash
zerg test [OPTIONS]
```

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--generate`, `-g` | flag | `false` | Generate test stubs for uncovered code |
| `--coverage`, `-c` | flag | `false` | Report test coverage |
| `--watch`, `-w` | flag | `false` | Watch mode (continuous testing) |
| `--parallel`, `-p` | integer | - | Number of parallel workers |
| `--framework` | choice | auto-detect | Framework: `pytest`, `jest`, `cargo`, `go`, `mocha`, `vitest` |
| `--path` | path | `.` | Path to test files |
| `--dry-run` | flag | `false` | Show what would run |
| `--json` | flag | `false` | Output as JSON |

**Auto-Detected Frameworks:**

| Language | Frameworks |
|----------|------------|
| Python | pytest, unittest |
| JavaScript/TypeScript | jest, mocha, vitest |
| Go | go test |
| Rust | cargo test |

**Examples:**

```bash
# Run all tests
zerg test

# Run with coverage report
zerg test --coverage

# Watch mode for TDD
zerg test --watch

# Parallel execution
zerg test --parallel 4

# Generate test stubs
zerg test --generate

# Specific framework
zerg test --framework pytest

# Test specific path
zerg test --path tests/unit/

# Preview test command
zerg test --dry-run

# JSON output for CI
zerg test --coverage --json
```

---

#### /zerg:build

**Build orchestration with error recovery.**

Auto-detects build system and executes with intelligent error recovery and retries.

**Usage:**
```bash
zerg build [OPTIONS]
```

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--target`, `-t` | string | `all` | Build target |
| `--mode`, `-m` | choice | `dev` | Build mode: `dev`, `staging`, `prod` |
| `--clean` | flag | `false` | Clean build artifacts first |
| `--watch`, `-w` | flag | `false` | Watch mode (rebuild on changes) |
| `--retry`, `-r` | integer | `3` | Retry attempts on failure |
| `--dry-run` | flag | `false` | Show what would be built |
| `--json` | flag | `false` | Output as JSON |

**Supported Build Systems:**

| Build System | Detection | Command |
|--------------|-----------|---------|
| npm | `package.json` | `npm run build` |
| cargo | `Cargo.toml` | `cargo build` |
| make | `Makefile` | `make` |
| gradle | `build.gradle` | `./gradlew build` |
| go | `go.mod` | `go build ./...` |
| python | `pyproject.toml` | `python -m build` |

**Examples:**

```bash
# Development build
zerg build

# Production build
zerg build --mode prod

# Clean build
zerg build --clean

# Watch mode
zerg build --watch

# Specific target
zerg build --target api

# Extended retries
zerg build --retry 5

# Preview command
zerg build --dry-run

# JSON output
zerg build --json
```

---

#### /zerg:analyze

**Static analysis, complexity metrics, and quality assessment.**

Executes linting, complexity analysis, coverage checking, and security scanning.

**Usage:**
```bash
zerg analyze [PATH] [OPTIONS]
```

**Arguments:**

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `PATH` | No | `.` | Path to analyze |

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--check`, `-c` | choice | `all` | Check type: `lint`, `complexity`, `coverage`, `security`, `all` |
| `--format`, `-f` | choice | `text` | Output format: `text`, `json`, `sarif` |
| `--threshold`, `-t` | string | - | Custom thresholds (e.g., `complexity=10,coverage=70`) |
| `--files` | path | - | Specific files (deprecated, use PATH) |

**Check Types:**

| Check | Tools | Description |
|-------|-------|-------------|
| `lint` | ruff, eslint, gofmt | Code style and formatting |
| `complexity` | radon, plato | Cyclomatic complexity |
| `coverage` | pytest-cov, istanbul | Test coverage |
| `security` | bandit, semgrep | Security vulnerabilities |
| `all` | All above | Complete analysis |

**Examples:**

```bash
# Run all checks
zerg analyze

# Lint check only
zerg analyze --check lint

# Security scan
zerg analyze --check security

# JSON output for CI
zerg analyze --format json

# SARIF for IDE integration
zerg analyze --format sarif

# Custom thresholds
zerg analyze --check complexity --threshold complexity=15

# Analyze specific path
zerg analyze src/

# Combined checks
zerg analyze src/ --check lint,security --format json
```

---

#### /zerg:review

**Two-stage code review workflow.**

Executes spec compliance check and code quality review in structured stages.

**Usage:**
```bash
zerg review [OPTIONS]
```

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--mode`, `-m` | choice | `full` | Review mode: `prepare`, `self`, `receive`, `full` |
| `--files`, `-f` | string | - | Specific files to review |
| `--output`, `-o` | path | - | Output file for results |
| `--json` | flag | `false` | Output as JSON |

**Review Modes:**

| Mode | Description | Output |
|------|-------------|--------|
| `prepare` | Generate change summary and checklist | PR description |
| `self` | Self-review checklist and analysis | Review checklist |
| `receive` | Process review feedback | Action items |
| `full` | Complete two-stage review | Full report |

**Examples:**

```bash
# Full two-stage review
zerg review

# Prepare PR description
zerg review --mode prepare

# Self-review before PR
zerg review --mode self

# Review specific files
zerg review --files "src/auth/*.py"

# Save report to file
zerg review --output review.md

# JSON output
zerg review --json

# Combined
zerg review --mode full --output review.md --json
```

---

### Development Commands

---

#### /zerg:refactor

**Automated code improvement and cleanup.**

Applies code quality transforms including dead code removal, simplification, type strengthening, and naming improvements.

**Usage:**
```bash
zerg refactor [PATH] [OPTIONS]
```

**Arguments:**

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `PATH` | No | `.` | Path to analyze |

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--transforms`, `-t` | string | all | Transforms: `dead-code`, `simplify`, `types`, `patterns`, `naming` |
| `--dry-run` | flag | `false` | Show suggestions without applying |
| `--interactive`, `-i` | flag | `false` | Interactive mode (approve each change) |
| `--files`, `-f` | string | - | Specific files (deprecated, use PATH) |
| `--json` | flag | `false` | Output as JSON |

**Transforms:**

| Transform | Description | Example |
|-----------|-------------|---------|
| `dead-code` | Remove unused code | Remove unused imports |
| `simplify` | Simplify expressions | `if x == True:` → `if x:` |
| `types` | Strengthen type hints | Replace `Any` with specific types |
| `patterns` | Apply design patterns | Extract repeated code |
| `naming` | Improve variable names | `x` → `user_count` |

**Examples:**

```bash
# Apply all transforms
zerg refactor

# Preview without applying
zerg refactor --dry-run

# Interactive mode
zerg refactor --interactive

# Specific transforms
zerg refactor --transforms dead-code,simplify

# Type improvements only
zerg refactor --transforms types

# Refactor specific path
zerg refactor src/auth/

# JSON output
zerg refactor --dry-run --json
```

---

#### /zerg:troubleshoot

**Systematic debugging with root cause analysis.**

Four-phase diagnostic process for identifying root causes of errors.

**Usage:**
```bash
zerg troubleshoot [OPTIONS]
```

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--error`, `-e` | string | - | Error message to analyze |
| `--stacktrace`, `-s` | path | - | Path to stack trace file |
| `--verbose`, `-v` | flag | `false` | Verbose output |
| `--output`, `-o` | path | - | Output file for diagnostic report |
| `--json` | flag | `false` | Output as JSON |

**Diagnostic Phases:**

1. **Symptom** - Parse error message/stack trace
2. **Hypothesis** - Generate possible causes
3. **Test** - Run diagnostic commands
4. **Root Cause** - Determine actual cause with confidence

**Examples:**

```bash
# Analyze error message
zerg troubleshoot --error "ValueError: invalid literal for int()"

# Analyze stack trace file
zerg troubleshoot --stacktrace error.log

# Verbose analysis
zerg troubleshoot --error "ImportError: No module named 'foo'" --verbose

# Save diagnostic report
zerg troubleshoot --error "ConnectionError" --output diagnostic.md

# JSON output
zerg troubleshoot --error "TypeError" --json
```

---

#### /zerg:git

**Git operations with intelligent commits and workflow management.**

Manages git operations with conventional commits and intelligent merge strategies.

**Usage:**
```bash
zerg git [OPTIONS]
```

**Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--action`, `-a` | choice | `commit` | Action: `commit`, `branch`, `merge`, `sync`, `history`, `finish` |
| `--push`, `-p` | flag | `false` | Push after commit |
| `--base`, `-b` | string | `main` | Base branch for operations |
| `--name`, `-n` | string | - | Branch name (for branch action) |
| `--branch` | string | - | Branch to merge (for merge action) |
| `--strategy` | choice | `squash` | Merge strategy: `merge`, `squash`, `rebase` |
| `--since` | string | - | Starting point for history |

**Actions:**

| Action | Description | Key Options |
|--------|-------------|-------------|
| `commit` | Intelligent conventional commit | `--push` |
| `branch` | Create/manage branches | `--name` |
| `merge` | Merge with strategy | `--branch`, `--strategy` |
| `sync` | Sync with remote | - |
| `history` | Generate changelog | `--since` |
| `finish` | Complete feature workflow | `--base` |

**Conventional Commit Types:**
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Tests
- `chore`: Maintenance

**Examples:**

```bash
# Commit with auto-generated message
zerg git --action commit

# Commit and push
zerg git --action commit --push

# Create feature branch
zerg git --action branch --name feature/auth

# Merge with squash
zerg git --action merge --branch feature/auth --strategy squash

# Sync with remote
zerg git --action sync

# Generate changelog
zerg git --action history --since v1.0.0

# Finish feature (interactive workflow)
zerg git --action finish --base main
```

---

### Infrastructure Commands

---

#### /zerg:security

**Security rules management.**

Manage secure coding rules from TikiTribe/claude-secure-coding-rules.

**Usage:**
```bash
zerg security-rules COMMAND [OPTIONS]
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `detect` | Detect project stack |
| `list` | List applicable rules |
| `fetch` | Download security rules |
| `integrate` | Full integration workflow |

**detect Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--path` | path | `.` | Project path |
| `--json-output` | flag | `false` | JSON output |

**list Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--path` | path | `.` | Project path |

**fetch Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--path` | path | `.` | Project path |
| `--output` | path | `.claude/security-rules/` | Output directory |
| `--no-cache` | flag | `false` | Force fresh download |

**integrate Options:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--path` | path | `.` | Project path |
| `--output` | path | `.claude/security-rules/` | Output directory |
| `--no-update-claude-md` | flag | `false` | Don't update CLAUDE.md |

**Examples:**

```bash
# Detect project stack
zerg security-rules detect

# JSON output for scripting
zerg security-rules detect --json-output

# List applicable rules
zerg security-rules list

# Download rules
zerg security-rules fetch

# Force fresh download
zerg security-rules fetch --no-cache

# Full integration
zerg security-rules integrate

# Custom output location
zerg security-rules fetch --output .claude/rules/
```

---

#### /zerg:worker

**Worker execution protocol (internal).**

Executed by orchestrator within containers/subprocesses. Not typically called directly by users.

**Environment Variables:**

| Variable | Description |
|----------|-------------|
| `ZERG_WORKER_ID` | Worker identifier (0-9) |
| `ZERG_FEATURE` | Feature name |
| `ZERG_BRANCH` | Git branch |
| `ZERG_SPEC_DIR` | Path to spec directory |
| `CLAUDE_CODE_TASK_LIST_ID` | Task list ID |

**Exit Codes:**

| Code | Meaning |
|------|---------|
| 0 | All tasks completed successfully |
| 1 | Unrecoverable error |
| 2 | Context limit reached (checkpoint) |
| 3 | All remaining tasks blocked |
| 130 | Interrupted (SIGINT) |

---

## Configuration

### Configuration File

ZERG configuration is stored in `.zerg/config.yaml`:

```yaml
version: "1.0"
project_type: python

workers:
  default_count: 5
  max_count: 10
  context_threshold: 0.7
  timeout_seconds: 3600

security:
  network_isolation: true
  filesystem_sandbox: true
  secrets_scanning: true

quality_gates:
  lint:
    command: "ruff check ."
    required: true
  typecheck:
    command: "mypy ."
    required: false
  test:
    command: "pytest"
    required: true

mcp_servers:
  - name: filesystem
    command: npx
    args: ["-y", "@anthropic/mcp-filesystem"]
```

### Worker Scaling Guidelines

| Workers | Best For | Notes |
|---------|----------|-------|
| 1-2 | Small features, learning | Lower API costs |
| 3-5 | Medium features | Balanced throughput |
| 6-10 | Large features | Maximum parallelism |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API authentication |
| `ZERG_LOG_LEVEL` | No | Logging verbosity: `debug`, `info`, `warn`, `error` |
| `ZERG_DEBUG` | No | Enable debug mode |

---

## Architecture

### Directory Structure

```
project/
├── .zerg/                          # ZERG runtime
│   ├── config.yaml                 # Configuration
│   ├── state/
│   │   └── {feature}.json          # Execution state
│   ├── logs/
│   │   ├── orchestrator.log        # Orchestrator output
│   │   └── worker-{id}.log         # Worker output
│   ├── worktrees/
│   │   └── {feature}-worker-N/     # Git worktrees
│   └── worker_entry.sh             # Worker startup script
│
├── .devcontainer/                  # Container configuration
│   ├── devcontainer.json           # VS Code devcontainer
│   ├── Dockerfile                  # Multi-language runtime
│   ├── post-create.sh              # Container init
│   ├── post-start.sh               # Worker startup
│   └── mcp-servers/
│       ├── config.json             # MCP server config
│       └── credentials.env.example # Credential template
│
├── .gsd/                           # GSD specification
│   ├── PROJECT.md                  # Project documentation
│   ├── INFRASTRUCTURE.md           # Infrastructure requirements
│   ├── STATE.md                    # Execution progress
│   ├── .current-feature            # Active feature marker
│   └── specs/
│       └── {feature}/
│           ├── requirements.md     # Feature requirements
│           ├── design.md           # Architecture
│           ├── task-graph.json     # Task definitions
│           └── worker-assignments.json
│
├── .claude/                        # Claude Code config
│   └── security-rules/             # Secure coding rules
│
└── CLAUDE.md                       # Project instructions
```

### Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    ZERG ORCHESTRATOR                         │
├─────────────────────────────────────────────────────────────┤
│  1. Load task-graph.json                                    │
│  2. Create git worktrees for each worker                    │
│  3. Spawn workers (subprocess or container)                 │
│  4. Assign tasks by level                                   │
│  5. Monitor progress                                        │
│  6. Merge branches after each level                         │
│  7. Run quality gates                                       │
│  8. Repeat until all levels complete                        │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  Worker 0          Worker 1          Worker 2               │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐           │
│  │ Worktree  │    │ Worktree  │    │ Worktree  │           │
│  │ Branch    │    │ Branch    │    │ Branch    │           │
│  │ Tasks     │    │ Tasks     │    │ Tasks     │           │
│  └───────────┘    └───────────┘    └───────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Workers Not Starting

**Symptoms:** Workers fail to spawn, container errors

**Solutions:**
```bash
# Check Docker is running
docker info

# Verify API key
echo $ANTHROPIC_API_KEY

# Check port availability
netstat -an | grep 49152

# Use subprocess mode (no Docker)
zerg rush --mode subprocess
```

### Tasks Failing Verification

**Symptoms:** Tasks marked as failed, verification errors

**Solutions:**
```bash
# Check worker logs
zerg logs --follow --level debug

# View specific task
cat .gsd/specs/{feature}/task-graph.json | jq '.tasks[] | select(.id == "TASK-001")'

# Troubleshoot error
zerg troubleshoot --error "verification error message"

# Retry with extended timeout
zerg retry TASK-001 --timeout 120
```

### Merge Conflicts

**Symptoms:** Merge fails, conflict state

**Solutions:**
```bash
# This should not happen with exclusive file ownership
# If it does, check task-graph.json for file overlap

# View conflict details
zerg status --verbose

# Abort and retry
zerg merge --abort
zerg retry --all-failed --reset

# Force merge (use with caution)
zerg merge --force
```

### Context Limit Reached

**Symptoms:** Worker exits with code 2, checkpoint messages

**Solutions:**
```bash
# This is normal behavior - workers checkpoint when context is full
# Simply resume execution
zerg rush --resume

# Use more workers to distribute context load
zerg rush --resume --workers 10
```

### Recovery Commands

```bash
# Resume interrupted execution
zerg rush --resume

# Check current state
zerg status --json

# Reset and restart specific level
zerg retry --level 2 --reset

# Clean everything and start fresh
zerg cleanup --all
zerg rush
```

---

## Tutorial

For a complete step-by-step tutorial building a Minerals Store ecommerce application, see:

**[Tutorial: Building a Minerals Store with ZERG](docs/tutorial-minerals-store.md)**

This tutorial covers:
- Project setup with Inception Mode
- Requirements planning with Socratic discovery
- Architecture design and task decomposition
- Parallel execution with devcontainers
- Security rules integration
- Quality gates and testing
- Final deployment

---

## License

MIT

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Support

- GitHub Issues: [github.com/rocklambros/zerg/issues](https://github.com/rocklambros/zerg/issues)
- Documentation: [github.com/rocklambros/zerg/wiki](https://github.com/rocklambros/zerg/wiki)
