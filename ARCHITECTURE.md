# ZERG Architecture

**Zero-Effort Rapid Growth** - Parallel Claude Code Execution System

ZERG is a distributed software development system that coordinates multiple Claude Code instances to build features in parallel. It combines spec-driven development (GSD methodology), level-based task execution, and git worktrees for isolated execution.

---

## Table of Contents

- [Core Principles](#core-principles)
- [System Layers](#system-layers)
- [Execution Flow](#execution-flow)
- [Module Reference](#module-reference)
- [Worker Execution Model](#worker-execution-model)
- [State Management](#state-management)
- [Quality Gates](#quality-gates)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Security Model](#security-model)
- [Configuration](#configuration)

---

## Core Principles

### Spec as Memory

Workers do not share conversation context. They share:
- `requirements.md` — what to build
- `design.md` — how to build it
- `task-graph.json` — atomic work units

This makes workers **stateless**. Any worker can pick up any task. Crash recovery is trivial.

### Exclusive File Ownership

Each task declares which files it creates or modifies. The design phase ensures no overlap within a level. This eliminates merge conflicts without runtime locking.

```json
{
  "id": "TASK-001",
  "files": {
    "create": ["src/models/user.py"],
    "modify": [],
    "read": ["src/config.py"]
  }
}
```

### Level-Based Execution

Tasks are organized into dependency levels:

| Level | Name | Description |
|-------|------|-------------|
| 1 | Foundation | Types, schemas, config |
| 2 | Core | Business logic, services |
| 3 | Integration | Wiring, endpoints |
| 4 | Testing | Unit and integration tests |
| 5 | Quality | Docs, cleanup |

All workers complete Level N before any proceed to N+1. The orchestrator merges all branches, runs quality gates, then signals workers to continue.

### Git Worktrees for Isolation

Each worker operates in its own git worktree with its own branch:

```
.zerg-worktrees/{feature}/worker-0/  →  branch: zerg/{feature}/worker-0
.zerg-worktrees/{feature}/worker-1/  →  branch: zerg/{feature}/worker-1
```

Workers commit independently. No filesystem conflicts.

---

## System Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                     Layer 1: Planning                           │
│          requirements.md + INFRASTRUCTURE.md                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Layer 2: Design                             │
│              design.md + task-graph.json                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Layer 3: Orchestration                         │
│   Worker lifecycle • Level sync • Branch merging • Monitoring   │
└─────────────────────────────────────────────────────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Worker 0   │     │  Worker 1   │     │  Worker N   │
│  (worktree) │     │  (worktree) │     │  (worktree) │
└─────────────┘     └─────────────┘     └─────────────┘
          │                   │                   │
          └───────────────────┴───────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Layer 4: Quality Gates                         │
│           Lint • Type-check • Test • Merge to main              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Execution Flow

### Planning Phase (`/zerg:plan`)

```
User Requirements → [Socratic Discovery] → requirements.md
                                                │
                                                ▼
                                    .gsd/specs/{feature}/requirements.md
```

### Design Phase (`/zerg:design`)

```
requirements.md → [Architecture Analysis] → task-graph.json + design.md
                                                │
                    ┌───────────────────────────┼───────────────────────────┐
                    ▼                           ▼                           ▼
            Level 1 Tasks              Level 2 Tasks              Level N Tasks
```

### Rush Phase (`/zerg:rush`)

```
[Orchestrator Start]
        │
        ▼
[Load task-graph.json] → [Assign tasks to workers]
        │
        ▼
[Create git worktrees]
        │
        ▼
[Spawn N worker processes]
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  FOR EACH LEVEL:                                                │
│    1. Workers execute tasks in PARALLEL                         │
│    2. Poll until all level tasks complete                       │
│    3. MERGE PROTOCOL:                                           │
│       • Merge all worker branches → staging                     │
│       • Run quality gates                                       │
│       • Promote staging → main                                  │
│    4. Rebase worker branches                                    │
│    5. Advance to next level                                     │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
[All tasks complete] ✓
```

### Worker Protocol

Each worker:

1. Loads `requirements.md`, `design.md`, `task-graph.json`
2. Reads `worker-assignments.json` for its tasks
3. For each level:
   - Pick next assigned task at current level
   - Read all dependency files
   - Implement the task
   - Run verification command
   - On pass: commit, mark complete
   - On fail: retry 3x, then mark blocked
4. After level complete: wait for merge signal
5. Pull merged changes
6. Continue to next level
7. At 70% context: commit WIP, exit (orchestrator restarts)

---

## Module Reference

### Core Modules (`zerg/`)

| Module | Lines | Purpose |
|--------|-------|---------|
| `orchestrator.py` | ~850 | Fleet management, level transitions, merge triggers |
| `levels.py` | ~350 | Level-based execution control, dependency enforcement |
| `state.py` | ~700 | Thread-safe file-based state persistence |
| `worker_protocol.py` | ~600 | Worker-side execution, Claude Code invocation |
| `launcher.py` | ~450 | Abstract worker spawning (subprocess/container) |

### Task Management

| Module | Lines | Purpose |
|--------|-------|---------|
| `assign.py` | ~200 | Task-to-worker assignment with load balancing |
| `parser.py` | ~195 | Parse and validate task graphs |
| `verify.py` | ~280 | Execute task verification commands |

### Git & Merge

| Module | Lines | Purpose |
|--------|-------|---------|
| `git_ops.py` | ~380 | Low-level git operations |
| `worktree.py` | ~300 | Git worktree management for worker isolation |
| `merge.py` | ~280 | Branch merging after each level |

### Quality & Security

| Module | Lines | Purpose |
|--------|-------|---------|
| `gates.py` | ~280 | Execute quality gates (lint, typecheck, test) |
| `security.py` | ~380 | Security validation, hook patterns |
| `validation.py` | ~340 | Task graph and ID validation |
| `command_executor.py` | ~530 | Safe command execution (no shell=True) |

### Configuration & Types

| Module | Lines | Purpose |
|--------|-------|---------|
| `config.py` | ~200 | Pydantic configuration management |
| `constants.py` | ~114 | Enumerations (TaskStatus, WorkerStatus, GateResult) |
| `types.py` | ~388 | TypedDict and dataclass definitions |

### CLI Commands (`zerg/commands/`)

| Command | Module | Purpose |
|---------|--------|---------|
| `/zerg:init` | `init.py` | Project initialization |
| `/zerg:plan` | `plan.py` | Capture requirements |
| `/zerg:design` | `design.py` | Generate architecture |
| `/zerg:rush` | `rush.py` | Launch parallel workers |
| `/zerg:status` | `status.py` | Progress monitoring |
| `/zerg:stop` | `stop.py` | Stop workers |
| `/zerg:retry` | `retry.py` | Retry failed tasks |
| `/zerg:logs` | `logs.py` | View worker logs |
| `/zerg:merge` | `merge_cmd.py` | Manual merge control |
| `/zerg:cleanup` | `cleanup.py` | Remove artifacts |

---

## Worker Execution Model

### Isolation Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                     WORKER ISOLATION LAYERS                     │
├─────────────────────────────────────────────────────────────────┤
│ 1. Git Worktree: .zerg-worktrees/{feature}-worker-{id}/         │
│    • Independent file system                                     │
│    • Separate git history                                        │
│    • Own branch: zerg/{feature}/worker-{id}                     │
├─────────────────────────────────────────────────────────────────┤
│ 2. Process Isolation                                            │
│    • Separate process per worker                                │
│    • Independent memory space                                    │
│    • Communication via state files                               │
├─────────────────────────────────────────────────────────────────┤
│ 3. Spec-Driven Execution                                        │
│    • No conversation history sharing                            │
│    • Read specs fresh each time                                 │
│    • Stateless, restartable                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Launcher Abstraction

```
WorkerLauncher (ABC)
├── SubprocessLauncher
│   ├── spawn() → subprocess.Popen
│   ├── monitor() → Check process status
│   └── terminate() → Kill process
│
└── ContainerLauncher
    ├── spawn() → docker run
    ├── monitor() → Check container status
    └── terminate() → Stop/kill container
```

Auto-detection: Uses `ContainerLauncher` if devcontainer.json exists and Docker is available, otherwise `SubprocessLauncher`.

### Context Management

- Monitor token usage via `ContextTracker`
- Checkpoint at 70% context threshold
- Worker exits gracefully (code 2)
- Orchestrator restarts worker from checkpoint

---

## State Management

### State File Structure

Location: `.zerg/state/{feature}.json`

```json
{
  "feature": "user-auth",
  "started_at": "2026-01-26T10:00:00",
  "current_level": 2,

  "tasks": {
    "TASK-001": {
      "status": "complete",
      "worker_id": 0,
      "started_at": "...",
      "completed_at": "...",
      "retry_count": 0
    }
  },

  "workers": {
    "0": {
      "status": "running",
      "current_task": "TASK-003",
      "tasks_completed": 2,
      "branch": "zerg/user-auth/worker-0"
    }
  },

  "levels": {
    "1": { "status": "complete", "merge_status": "complete" },
    "2": { "status": "running", "merge_status": "pending" }
  }
}
```

### Task Status Transitions

```
pending → claimed → in_progress → verifying → complete
                                           ↘ failed → retry?
```

### Thread Safety

- **RLock**: Guards all state mutations
- **Atomic writes**: Full file replacement
- **Timestamps**: Enable recovery and debugging

---

## Quality Gates

### Task Verification (Per-Task)

```json
{
  "id": "TASK-001",
  "verification": {
    "command": "python -c \"from src.models.user import User\"",
    "timeout_seconds": 60
  }
}
```

### Level Quality Gates (Per-Level)

Configuration in `.zerg/config.yaml`:

```yaml
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
```

### Gate Results

| Result | Description | Action |
|--------|-------------|--------|
| `pass` | Exit code 0 | Continue |
| `fail` | Non-zero exit | Block if required |
| `timeout` | Exceeded limit | Treat as failure |
| `error` | Couldn't execute | Pause for intervention |

---

## Pre-commit Hooks

ZERG includes comprehensive pre-commit hooks at `.zerg/hooks/pre-commit`.

### Security Checks (Block Commit)

| Check | Pattern | Description |
|-------|---------|-------------|
| AWS Keys | `AKIA[0-9A-Z]{16}` | AWS Access Key IDs |
| GitHub PATs | `ghp_[a-zA-Z0-9]{36}` | Personal Access Tokens |
| OpenAI Keys | `sk-[a-zA-Z0-9]{48}` | OpenAI API Keys |
| Anthropic Keys | `sk-ant-[a-zA-Z0-9_-]+` | Anthropic API Keys |
| Private Keys | `-----BEGIN * PRIVATE KEY-----` | Key headers |
| Shell Injection | `shell=True`, `os.system()` | Dangerous patterns |
| Code Injection | `eval()`, `exec()` | Dynamic code execution |
| Pickle | `pickle.load()` | Unsafe deserialization |
| Sensitive Files | `.env`, `credentials.json` | Credential files |

### Quality Checks (Warn Only)

| Check | Description |
|-------|-------------|
| Ruff Lint | Style issues in Python files |
| Debugger | `breakpoint()`, `pdb.set_trace()` |
| Merge Markers | Unresolved `<<<<<<<` conflicts |
| Large Files | Files >5MB |

### ZERG-Specific Checks (Warn Only)

| Check | Validation |
|-------|------------|
| Branch Naming | `zerg/{feature}/worker-{N}` format |
| Print Statements | `print()` in `zerg/` directory |
| Hardcoded URLs | `localhost:PORT` outside tests |

### Exempt Paths

- `tests/`, `fixtures/`
- `*_test.py`, `test_*.py`
- `conftest.py`

### Hook Patterns in Code

Patterns are defined in `zerg/security.py`:

```python
HOOK_PATTERNS = {
    "security": {
        "aws_key": r"AKIA[0-9A-Z]{16}",
        "github_pat": r"(ghp_[a-zA-Z0-9]{36}|github_pat_...)",
        ...
    },
    "quality": {
        "debugger": r"(breakpoint\s*\(\)|pdb\.set_trace\s*\(\))",
        ...
    }
}
```

---

## Security Model

### Environment Variable Filtering

```python
ALLOWED_ENV_VARS = {
    "ZERG_WORKER_ID", "ZERG_FEATURE", "ZERG_WORKTREE",
    "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
    "CI", "DEBUG", "LOG_LEVEL"
}

DANGEROUS_ENV_VARS = {
    "LD_PRELOAD", "DYLD_INSERT_LIBRARIES",
    "PYTHONPATH", "HOME", "USER", "SHELL"
}
```

### Command Execution Safety

| Protection | Implementation |
|------------|----------------|
| No shell=True | Commands parsed explicitly |
| Allowlist | Commands checked against config |
| Timeout | Every command has max duration |
| Output capture | Separate stdout/stderr |

### Task ID Validation

```
Pattern: [A-Za-z][A-Za-z0-9_-]{0,63}

Rejects:
  • Shell metacharacters (;|&`$)
  • Path traversal (../)
  • Excessive length (>64 chars)
```

---

## Configuration

### Configuration File

Location: `.zerg/config.yaml`

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
  test:
    command: "pytest"
    required: true

hooks:
  pre_commit:
    enabled: true
    security_checks:
      secrets_detection: true
      shell_injection: true
      block_on_violation: true
    quality_checks:
      ruff_lint: true
      warn_on_violation: true

mcp_servers:
  - name: filesystem
    command: npx
    args: ["-y", "@anthropic/mcp-filesystem"]
```

---

## Directory Structure

```
project/
├── .zerg/
│   ├── config.yaml          # ZERG configuration
│   ├── hooks/
│   │   └── pre-commit       # Pre-commit hook script
│   ├── state/               # Runtime state
│   │   └── {feature}.json
│   └── logs/                # Worker logs
│
├── .zerg-worktrees/         # Git worktrees (gitignored)
│   └── {feature}-worker-N/
│
├── .gsd/
│   ├── PROJECT.md
│   ├── STATE.md             # Human-readable progress
│   └── specs/{feature}/
│       ├── requirements.md
│       ├── design.md
│       └── task-graph.json
│
├── .devcontainer/
│   ├── devcontainer.json
│   └── Dockerfile
│
└── zerg/                    # Source code (35+ modules)
```

---

## Error Handling

| Scenario | Response |
|----------|----------|
| Task verification fails | Retry 3x, then mark blocked |
| Worker crashes | Orchestrator detects, respawns |
| Merge conflict | Pause for human intervention |
| All workers blocked | Pause ZERG, alert human |
| Context limit (70%) | Commit WIP, exit for restart |

---

## Scaling Guidelines

| Workers | Use Case |
|---------|----------|
| 1-2 | Small features, learning |
| 3-5 | Medium features, balanced |
| 6-10 | Large features, max throughput |

Diminishing returns beyond the widest level's parallelizable tasks.

---

## Summary

ZERG enables rapid parallel development through:

1. **Spec-driven execution** — Workers read specifications, not conversation history
2. **Exclusive file ownership** — No merge conflicts possible within levels
3. **Level-based dependencies** — Proper sequencing guaranteed
4. **Resilient workers** — Automatic retry and checkpoint recovery
5. **Quality gates** — Automated verification at every stage
6. **Security by design** — Strict validation and pre-commit hooks

The result: Complex features developed rapidly through coordinated parallel execution while maintaining code quality and preventing conflicts.
