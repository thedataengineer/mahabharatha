# MAHABHARATHA Implementation Task Backlog

**Phase**: 3 - Implementation Planning
**Date**: January 25, 2026
**Status**: COMPLETE
**Methodology**: MAHABHARATHA self-application (manual execution)
**Completed**: January 31, 2026

---

## Executive Summary

This backlog contained 42 atomic tasks to build MAHABHARATHA from the Phase 2 architecture specification. All 42 tasks are now complete. Implementation exceeded the original specification — the codebase includes additional components not in Phase 3 scope (worker_metrics, task_sync, context_engineering plugin, harness, TUI dashboard).

**Critical Path**: MAHABHARATHA-L1-001 → MAHABHARATHA-L1-003 → MAHABHARATHA-L2-001 → MAHABHARATHA-L2-004 → MAHABHARATHA-L3-001 → MAHABHARATHA-L3-004 → MAHABHARATHA-L4-004 → MAHABHARATHA-L5-003

---

## Progress Tracker

| Level | Name | Total | Complete | Blocked | Remaining |
|-------|------|-------|----------|---------|-----------|
| 1 | Foundation | 8 | 8 | 0 | 0 |
| 2 | Core | 10 | 10 | 0 | 0 |
| 3 | Integration | 9 | 9 | 0 | 0 |
| 4 | Commands | 10 | 10 | 0 | 0 |
| 5 | Quality | 5 | 5 | 0 | 0 |
| **Total** | | **42** | **42** | **0** | **0** |

**Last Updated**: 2026-01-31T12:00:00Z

---

## Level 1: Foundation

*Types, schemas, configuration, and package structure. No dependencies.*

### MAHABHARATHA-L1-001: Python Package Structure ⭐ CRITICAL PATH

| Attribute | Value |
|-----------|-------|
| **Description** | Create Python package skeleton with proper module layout |
| **Files Create** | `mahabharatha/__init__.py`, `mahabharatha/py.typed`, `pyproject.toml`, `requirements.txt` |
| **Verification** | `python -c "import mahabharatha; print(mahabharatha.__version__)"` |
| **Status** | DONE |

---

### MAHABHARATHA-L1-002: Type Definitions

| Attribute | Value |
|-----------|-------|
| **Description** | Define TypedDict and dataclass types for all domain objects |
| **Files Create** | `mahabharatha/types.py` |
| **Verification** | `python -c "from mahabharatha.types import TaskGraph, WorkerState, LevelStatus"` |
| **Status** | DONE |

---

### MAHABHARATHA-L1-003: Configuration Schema ⭐ CRITICAL PATH

| Attribute | Value |
|-----------|-------|
| **Description** | Config loader with Pydantic validation, defaults from config.yaml |
| **Files Create** | `mahabharatha/config.py` |
| **Verification** | `python -c "from mahabharatha.config import ZergConfig; c = ZergConfig.load(); print(c.workers.max_concurrent)"` |
| **Status** | DONE |

---

### MAHABHARATHA-L1-004: Constants and Enums

| Attribute | Value |
|-----------|-------|
| **Description** | Define level names, task statuses, gate results, error codes |
| **Files Create** | `mahabharatha/constants.py` |
| **Verification** | `python -c "from mahabharatha.constants import Level, TaskStatus, GateResult"` |
| **Status** | DONE |

---

### MAHABHARATHA-L1-005: Logging Setup

| Attribute | Value |
|-----------|-------|
| **Description** | Structured JSON logging with worker ID context, file rotation |
| **Files Create** | `mahabharatha/logging.py` |
| **Verification** | `python -c "from mahabharatha.logging import get_logger; log = get_logger('test'); log.info('works')"` |
| **Status** | DONE |

---

### MAHABHARATHA-L1-006: Exception Hierarchy

| Attribute | Value |
|-----------|-------|
| **Description** | Define ZergError base and specific exceptions for each failure mode |
| **Files Create** | `mahabharatha/exceptions.py` |
| **Verification** | `python -c "from mahabharatha.exceptions import ZergError, TaskVerificationFailed, MergeConflict"` |
| **Status** | DONE |

---

### MAHABHARATHA-L1-007: Task Graph Schema Validator

| Attribute | Value |
|-----------|-------|
| **Description** | JSON Schema for task-graph.json with validation functions |
| **Files Create** | `mahabharatha/schemas/task_graph.json`, `mahabharatha/schemas/__init__.py`, `mahabharatha/validation.py` |
| **Verification** | `python -c "from mahabharatha.validation import validate_task_graph"` |
| **Status** | DONE |
| **Notes** | Schema in `mahabharatha/schemas/`, validation in `mahabharatha/validation.py` |

---

### MAHABHARATHA-L1-008: CLI Entry Point Skeleton

| Attribute | Value |
|-----------|-------|
| **Description** | Click-based CLI with subcommand structure |
| **Files Create** | `mahabharatha/cli.py` |
| **Verification** | `python -m mahabharatha --help` |
| **Status** | DONE |

---

## Level 2: Core

*Business logic components. Depend on Level 1 foundation.*

### MAHABHARATHA-L2-001: Worktree Manager ⭐ CRITICAL PATH

| Attribute | Value |
|-----------|-------|
| **Description** | Git worktree create/delete/list, branch management, path resolution |
| **Files Create** | `mahabharatha/worktree.py` |
| **Verification** | `python -c "from mahabharatha.worktree import WorktreeManager"` |
| **Status** | DONE |

---

### MAHABHARATHA-L2-002: Port Allocator

| Attribute | Value |
|-----------|-------|
| **Description** | Random port selection in ephemeral range, collision detection, tracking |
| **Files Create** | `mahabharatha/ports.py` |
| **Verification** | `python -c "from mahabharatha.ports import PortAllocator"` |
| **Status** | DONE |

---

### MAHABHARATHA-L2-003: Task Parser

| Attribute | Value |
|-----------|-------|
| **Description** | Load task-graph.json, parse into domain objects, validate dependencies |
| **Files Create** | `mahabharatha/parser.py` |
| **Verification** | `python -c "from mahabharatha.parser import TaskParser"` |
| **Status** | DONE |

---

### MAHABHARATHA-L2-004: Level Controller ⭐ CRITICAL PATH

| Attribute | Value |
|-----------|-------|
| **Description** | Track level completion, block N+1 until N done, emit level events |
| **Files Create** | `mahabharatha/levels.py` |
| **Verification** | `python -c "from mahabharatha.levels import LevelController"` |
| **Status** | DONE |
| **Notes** | Includes `is_level_complete()` (success-only) and `is_level_resolved()` (all-terminal) split. Fixed in commit 2451f86. |

---

### MAHABHARATHA-L2-005: State Manager (Claude Tasks Integration)

| Attribute | Value |
|-----------|-------|
| **Description** | Adapter for Claude Native Tasks API, state persistence, polling |
| **Files Create** | `mahabharatha/state.py` |
| **Verification** | `python -c "from mahabharatha.state import StateManager"` |
| **Status** | DONE |

---

### MAHABHARATHA-L2-006: Quality Gate Runner

| Attribute | Value |
|-----------|-------|
| **Description** | Execute gate commands, capture output, determine pass/fail, timeout handling |
| **Files Create** | `mahabharatha/gates.py` |
| **Verification** | `python -c "from mahabharatha.gates import GateRunner"` |
| **Status** | DONE |

---

### MAHABHARATHA-L2-007: Verification Executor

| Attribute | Value |
|-----------|-------|
| **Description** | Run task verification commands, handle timeouts, capture results |
| **Files Create** | `mahabharatha/verify.py` |
| **Verification** | `python -c "from mahabharatha.verify import VerificationExecutor"` |
| **Status** | DONE |

---

### MAHABHARATHA-L2-008: Worker Assignment Calculator

| Attribute | Value |
|-----------|-------|
| **Description** | Distribute tasks to workers, balance by level, respect file ownership |
| **Files Create** | `mahabharatha/assign.py` |
| **Verification** | `python -c "from mahabharatha.assign import WorkerAssignment"` |
| **Status** | DONE |

---

### MAHABHARATHA-L2-009: Container Manager

| Attribute | Value |
|-----------|-------|
| **Description** | Docker/devcontainer lifecycle: build, start, stop, health check |
| **Files Create** | `mahabharatha/containers.py` |
| **Verification** | `python -c "from mahabharatha.containers import ContainerManager"` |
| **Status** | DONE |
| **Notes** | Integrated into `mahabharatha/launcher.py` as `ContainerLauncher` class |

---

### MAHABHARATHA-L2-010: Git Operations

| Attribute | Value |
|-----------|-------|
| **Description** | Branch create/delete, merge, rebase, conflict detection, staging branch |
| **Files Create** | `mahabharatha/git_ops.py` |
| **Verification** | `python -c "from mahabharatha.git_ops import GitOps"` |
| **Status** | DONE |

---

## Level 3: Integration

*Wire components together into working subsystems. Depend on Level 2.*

### MAHABHARATHA-L3-001: Orchestrator Core ⭐ CRITICAL PATH

| Attribute | Value |
|-----------|-------|
| **Description** | Main event loop: worker lifecycle, level transitions, status polling |
| **Files Create** | `mahabharatha/orchestrator.py` |
| **Verification** | `python -c "from mahabharatha.orchestrator import Orchestrator"` |
| **Status** | DONE |
| **Notes** | ~1500 lines. Uses `is_level_resolved()` for advancement. Includes level_coordinator delegation. |

---

### MAHABHARATHA-L3-002: Merge Gate Integration

| Attribute | Value |
|-----------|-------|
| **Description** | Combine git ops + quality gates + level controller for merge workflow |
| **Files Create** | `mahabharatha/merge.py` |
| **Verification** | `python -c "from mahabharatha.merge import MergeCoordinator"` |
| **Status** | DONE |

---

### MAHABHARATHA-L3-003: Worker Protocol Handler

| Attribute | Value |
|-----------|-------|
| **Description** | Worker startup sequence, task claiming, completion reporting, exit handling |
| **Files Create** | `mahabharatha/worker_protocol.py` |
| **Verification** | `python -c "from mahabharatha.worker_protocol import WorkerProtocol"` |
| **Status** | DONE |

---

### MAHABHARATHA-L3-004: Kurukshetra Command Implementation ⭐ CRITICAL PATH

| Attribute | Value |
|-----------|-------|
| **Description** | Full /mahabharatha kurukshetra flow: parse graph, assign workers, launch containers, monitor |
| **Files Create** | `mahabharatha/commands/kurukshetra.py` |
| **Verification** | `python -m mahabharatha kurukshetra --help` |
| **Status** | DONE |
| **Notes** | Supports subprocess, container, and task modes |

---

### MAHABHARATHA-L3-005: Status Command Implementation

| Attribute | Value |
|-----------|-------|
| **Description** | /mahabharatha status output: progress bars, worker table, event log |
| **Files Create** | `mahabharatha/commands/status.py` |
| **Verification** | `python -m mahabharatha status --help` |
| **Status** | DONE |

---

### MAHABHARATHA-L3-006: Stop Command Implementation

| Attribute | Value |
|-----------|-------|
| **Description** | /mahabharatha stop flow: graceful shutdown, checkpoint, container cleanup |
| **Files Create** | `mahabharatha/commands/stop.py` |
| **Verification** | `python -m mahabharatha stop --help` |
| **Status** | DONE |

---

### MAHABHARATHA-L3-007: Retry Command Implementation

| Attribute | Value |
|-----------|-------|
| **Description** | /mahabharatha retry flow: reset task state, re-queue for execution |
| **Files Create** | `mahabharatha/commands/retry.py` |
| **Verification** | `python -m mahabharatha retry --help` |
| **Status** | DONE |

---

### MAHABHARATHA-L3-008: Logs Command Implementation

| Attribute | Value |
|-----------|-------|
| **Description** | /mahabharatha logs: stream worker logs, filtering, tail/follow modes |
| **Files Create** | `mahabharatha/commands/logs.py` |
| **Verification** | `python -m mahabharatha logs --help` |
| **Status** | DONE |

---

### MAHABHARATHA-L3-009: Cleanup Command Implementation

| Attribute | Value |
|-----------|-------|
| **Description** | /mahabharatha cleanup: remove worktrees, branches, logs, containers |
| **Files Create** | `mahabharatha/commands/cleanup.py` |
| **Verification** | `python -m mahabharatha cleanup --help` |
| **Status** | DONE |

---

## Level 4: Commands

*Slash command prompt refinement and integration. Depend on Level 3.*

**Note**: Command files relocated from `.claude/commands/` to `mahabharatha/data/commands/` during implementation. All 19 command files exist at the new path.

### MAHABHARATHA-L4-001: Init Command Refinement

| Attribute | Value |
|-----------|-------|
| **Description** | Update /mahabharatha init prompt with detection logic, generate config |
| **Files** | `mahabharatha/data/commands/mahabharatha:init.md` |
| **Status** | DONE |

---

### MAHABHARATHA-L4-002: Plan Command Refinement

| Attribute | Value |
|-----------|-------|
| **Description** | Update /mahabharatha plan prompt with requirements template, approval flow |
| **Files** | `mahabharatha/data/commands/mahabharatha:plan.md`, `mahabharatha:plan.core.md` |
| **Status** | DONE |

---

### MAHABHARATHA-L4-003: Design Command Refinement

| Attribute | Value |
|-----------|-------|
| **Description** | Update /mahabharatha design prompt with task graph generation, validation |
| **Files** | `mahabharatha/data/commands/mahabharatha:design.md`, `mahabharatha:design.core.md` |
| **Status** | DONE |

---

### MAHABHARATHA-L4-004: Kurukshetra Command Prompt Update ⭐ CRITICAL PATH

| Attribute | Value |
|-----------|-------|
| **Description** | Sync /mahabharatha kurukshetra prompt with Python implementation, add examples |
| **Files** | `mahabharatha/data/commands/mahabharatha:kurukshetra.md`, `mahabharatha:kurukshetra.core.md` |
| **Status** | DONE |

---

### MAHABHARATHA-L4-005: Status Command Prompt Update

| Attribute | Value |
|-----------|-------|
| **Description** | Sync /mahabharatha status prompt with Python implementation |
| **Files** | `mahabharatha/data/commands/mahabharatha:status.md`, `mahabharatha:status.core.md` |
| **Status** | DONE |

---

### MAHABHARATHA-L4-006: Worker Command Refinement

| Attribute | Value |
|-----------|-------|
| **Description** | Update /mahabharatha worker prompt with protocol, context handling, exit codes |
| **Files** | `mahabharatha/data/commands/mahabharatha:worker.md`, `mahabharatha:worker.core.md` |
| **Status** | DONE |

---

### MAHABHARATHA-L4-007: Merge Command Creation

| Attribute | Value |
|-----------|-------|
| **Description** | Create /mahabharatha merge prompt for manual gate triggering |
| **Files** | `mahabharatha/data/commands/mahabharatha:merge.md`, `mahabharatha:merge.core.md` |
| **Status** | DONE |

---

### MAHABHARATHA-L4-008: Logs Command Prompt Creation

| Attribute | Value |
|-----------|-------|
| **Description** | Create /mahabharatha logs prompt with filtering, streaming examples |
| **Files** | `mahabharatha/data/commands/mahabharatha:logs.md` |
| **Status** | DONE |

---

### MAHABHARATHA-L4-009: Stop Command Prompt Creation

| Attribute | Value |
|-----------|-------|
| **Description** | Create /mahabharatha stop prompt with graceful/force options |
| **Files** | `mahabharatha/data/commands/mahabharatha:stop.md` |
| **Status** | DONE |

---

### MAHABHARATHA-L4-010: Cleanup Command Prompt Creation

| Attribute | Value |
|-----------|-------|
| **Description** | Create /mahabharatha cleanup prompt with options documentation |
| **Files** | `mahabharatha/data/commands/mahabharatha:cleanup.md` |
| **Status** | DONE |

---

## Level 5: Quality

*Testing, security, and documentation. Depend on Level 4.*

### MAHABHARATHA-L5-001: Unit Tests Foundation

| Attribute | Value |
|-----------|-------|
| **Description** | Pytest setup, fixtures, test utilities for core components |
| **Files Create** | `tests/__init__.py`, `tests/conftest.py`, `tests/test_config.py`, `tests/test_types.py` |
| **Verification** | `pytest tests/test_config.py tests/test_types.py -v` |
| **Status** | DONE |
| **Notes** | Test suite: 5418 passed, 0 failed, 1 skipped |

---

### MAHABHARATHA-L5-002: Core Component Tests

| Attribute | Value |
|-----------|-------|
| **Description** | Tests for worktree, levels, gates, verification, git ops |
| **Files** | `tests/test_worktree.py`, `tests/test_levels.py`, `tests/test_gates.py`, `tests/test_git_ops.py` |
| **Verification** | `pytest tests/test_levels.py tests/test_gates.py tests/test_git_ops.py -v` |
| **Status** | DONE |

---

### MAHABHARATHA-L5-003: Integration Tests ⭐ CRITICAL PATH

| Attribute | Value |
|-----------|-------|
| **Description** | End-to-end tests: kurukshetra with mock containers, level progression, merge flow |
| **Files** | `tests/integration/`, `tests/e2e/` |
| **Verification** | `pytest tests/integration/ tests/e2e/ -v` |
| **Status** | DONE |
| **Notes** | Includes test_rush_flow, test_merge_flow, test_full_pipeline, test_multilevel_execution, test_bugfix_e2e |

---

### MAHABHARATHA-L5-004: Security Hooks

| Attribute | Value |
|-----------|-------|
| **Description** | Security rules and validation |
| **Files** | `.claude/rules/security/` |
| **Status** | DONE |
| **Notes** | Implemented as `.claude/rules/security/` directory with OWASP, Docker, JS, and Python rules |

---

### MAHABHARATHA-L5-005: Documentation Update

| Attribute | Value |
|-----------|-------|
| **Description** | Update README, CLAUDE.md with final implementation details |
| **Files** | `README.md`, `CLAUDE.md` |
| **Status** | DONE |

---

## Completion Checklist

### Level 1 Complete When:
- [x] `python -c "import mahabharatha"` succeeds
- [x] `python -m mahabharatha --help` shows commands
- [x] Config loads from `.mahabharatha/config.yaml`
- [x] All types importable

### Level 2 Complete When:
- [x] Worktree create/delete works in test repo
- [x] Level controller blocks correctly
- [x] Quality gate runner executes commands
- [x] Container manager starts test container

### Level 3 Complete When:
- [x] Orchestrator event loop runs
- [x] `/mahabharatha kurukshetra` launches workers (dry-run)
- [x] `/mahabharatha status` shows progress
- [x] Merge gate executes quality checks

### Level 4 Complete When:
- [x] All slash command prompts updated
- [x] New commands (merge, logs, stop, cleanup) have prompts
- [x] CLI subcommands match prompts

### Level 5 Complete When:
- [x] `pytest` passes (5418 passed, 0 failed, 1 skipped)
- [x] Integration tests pass
- [x] Security rules configured
- [x] README has installation instructions

---

## Implementation Notes

### File Location Change
Command files were relocated from `.claude/commands/mahabharatha:*.md` to `mahabharatha/data/commands/mahabharatha:*.md` during implementation. The `mahabharatha/data/` package serves command files programmatically.

### Beyond Phase 3 Scope
The implementation includes components not in the original 42-task backlog:
- `mahabharatha/worker_metrics.py` — Worker performance metrics collection
- `mahabharatha/task_sync.py` — TaskSyncBridge for Claude Task system coordination
- `mahabharatha/level_coordinator.py` — Level completion delegation from orchestrator
- `mahabharatha/context_engineering/` — Context engineering plugin (command splitting, task-scoped context)
- `tests/e2e/harness.py` — E2E test harness for mock pipeline execution
- `mahabharatha/dashboard.py` — TUI dashboard for live monitoring
- `mahabharatha/worker_main.py` — Worker entry point and subprocess management

### Key Bug Fixes (Post-Implementation)
- **Commit 2451f86**: Fixed `is_level_complete` vs `is_level_resolved` semantics, mock worker task ID mismatch, MetricsCollector patch location
- **Commit 5dda781**: Wired `CLAUDE_CODE_TASK_LIST_ID` through Python execution layer

### Test Results (2026-01-31)
```
5418 passed, 0 failed, 1 skipped (100% pass rate on non-skipped)
Duration: 5m55s
```

---

## Session Log

### 2026-01-25
- Created initial task backlog from Phase 2 architecture
- Identified 42 atomic tasks across 5 levels
- Critical path: 5.5 hours minimum

### 2026-01-25 through 2026-01-30
- All 42 tasks implemented across multiple sessions
- Additional components built beyond Phase 3 scope

### 2026-01-31
- Final audit: 42/42 tasks DONE
- All test failures resolved (5418 passed)
- Backlog marked COMPLETE
