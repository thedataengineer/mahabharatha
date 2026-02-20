# Orchestrator & Schema Fixes - Task Backlog

**Feature**: orchestrator-fixes
**Status**: ✅ Complete (12/12)
**Created**: 2026-01-27
**Updated**: 2026-01-27
**Total Tasks**: 12 | **Levels**: 5 | **Max Parallelization**: 4

---

## Root Cause Analysis

### Schema Issues (Discovered in DC-012)
| Issue | Location | Impact |
|-------|----------|--------|
| Dual schema conflict | `.mahabharatha/schemas/` vs `mahabharatha/schemas/` | Validation inconsistency |
| Level 0 allowed | `.mahabharatha/schemas/task-graph.schema.json:21` | 0-indexed vs 1-indexed confusion |
| Files structure mismatch | Schema 1 requires all, Schema 2 optional | Unpredictable validation |
| ID pattern inconsistency | Strict vs relaxed patterns | Task ID validation failures |

### Orchestrator Issues (Discovered in kurukshetra execution)
| Issue | Severity | Location | Impact |
|-------|----------|----------|--------|
| Worker deletion + restart race | CRITICAL | `orchestrator.py:579,701` | Workers lost, state corruption |
| Poll loop inconsistency | CRITICAL | `orchestrator.py:611` | Orphaned processes |
| Missing worktree cleanup | HIGH | `orchestrator.py:703` | Duplicate worktrees |
| Spawn failure handling | HIGH | `orchestrator.py:545` | Under-parallelization |
| Worker init race | MEDIUM | `orchestrator.py:227` | Early crashes |
| Launcher state sync | MEDIUM | `orchestrator.py:579,561` | Stale status |

---

## Execution Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 12 |
| Completed | 0 |
| Remaining | 12 |
| Levels | 5 |
| Max Parallelization | 4 (Level 1 & 2) |
| Critical Path | OFX-001 -> OFX-005 -> OFX-009 -> OFX-011 -> OFX-012 |
| Est. Sessions | 2-3 |

---

## Level 1: Test Infrastructure (Parallel: 4 tasks) ✅

| ID | Task | Files Owned | Status | Verification |
|----|------|-------------|--------|--------------|
| **OFX-001** ⭐ | Schema validation tests | `tests/unit/test_schema_validation.py` | ✅ Complete | 27 tests pass |
| **OFX-002** | Worker lifecycle tests | `tests/unit/test_worker_lifecycle.py` | ✅ Complete | 18 tests pass |
| **OFX-003** | State sync tests | `tests/unit/test_state_sync.py` | ✅ Complete | 16 tests pass |
| **OFX-004** | Orchestrator integration tests | `tests/integration/test_orchestrator_fixes.py` | ✅ Complete | 14 tests pass |

**Test Coverage Requirements:**
- OFX-001: Level bounds, files structure, ID patterns, schema loading
- OFX-002: Spawn, terminate, restart, state transitions, worktree cleanup
- OFX-003: Orchestrator-launcher sync, handle consistency, status accuracy
- OFX-004: Full lifecycle, level transitions, failure recovery, init wait

---

## Level 2: Core Implementation (Parallel: 4 tasks) ✅

| ID | Task | Files Owned | Deps | Status | Verification |
|----|------|-------------|------|--------|--------------|
| **OFX-005** ⭐ | Consolidate schema | `mahabharatha/schemas/task_graph.json`, `.mahabharatha/task_graph.py` | OFX-001 | ✅ Complete | Old schema archived |
| **OFX-006** | Update validation | `mahabharatha/validation.py` | OFX-001 | ✅ Complete | Level >= 1 enforced |
| **OFX-007** ⭐ | Fix orchestrator | `mahabharatha/orchestrator.py` | OFX-002 | ✅ Complete | Poll loop fixed, init wait added |
| **OFX-008** | Fix launcher sync | `mahabharatha/launcher.py` | OFX-003 | ✅ Complete | sync_state() added |

**Implementation Details:**
- OFX-005: Single schema, archive old to `.mahabharatha/schemas/archived/`, add to .gitignore, level >= 1
- OFX-006: Level check, files validation, better errors
- OFX-007: Termination race, poll loop, worktree cleanup, spawn handling, WorkerTracker (top-level class), init wait (600s timeout)
- OFX-008: sync_state() method, state reconciliation

---

## Level 3: Integration (Parallel: 2 tasks) ✅

| ID | Task | Files Owned | Deps | Status | Verification |
|----|------|-------------|------|--------|--------------|
| **OFX-009** ⭐ | Parser integration | `mahabharatha/parser.py` | OFX-005,OFX-006 | ✅ Complete | Uses validation correctly |
| **OFX-010** | Design command | `mahabharatha/commands/design.py` | OFX-005,OFX-006 | ✅ Complete | Generates level >= 1 |

---

## Level 4: Documentation (Sequential: 1 task) ✅

| ID | Task | Files Owned | Deps | Status | Verification |
|----|------|-------------|------|--------|--------------|
| **OFX-011** | Skill docs | `mahabharatha:kurukshetra.md`, `mahabharatha:design.md` | OFX-010 | ✅ Complete | Already shows level >= 1 |

---

## Level 5: Final Verification (Sequential: 1 task) ✅

| ID | Task | Files Owned | Deps | Status | Verification |
|----|------|-------------|------|--------|--------------|
| **OFX-012** ⭐ | Final tests | `tests/integration/test_full_rush_cycle.py` | All | ✅ Complete | 93 tests pass |

---

## Critical Path ⭐

```
OFX-001 (30m) ─── Schema validation tests
       │
       ▼
OFX-005 (25m) ─── Consolidate schema
       │
       ▼
OFX-009 (15m) ─── Parser integration
       │
       ▼
OFX-011 (15m) ─── Skill docs
       │
       ▼
OFX-012 (30m) ─── Final tests

═══════════════════════════════════════
Total Critical Path: ~115 minutes (2 hours)
```

---

## File Ownership Matrix

| File | Owner | Action | Status |
|------|-------|--------|--------|
| `tests/unit/test_schema_validation.py` | OFX-001 | Create | ⬜ |
| `tests/unit/test_worker_lifecycle.py` | OFX-002 | Create | ⬜ |
| `tests/unit/test_state_sync.py` | OFX-003 | Create | ⬜ |
| `tests/integration/test_orchestrator_fixes.py` | OFX-004 | Create | ⬜ |
| `mahabharatha/schemas/task_graph.json` | OFX-005 | Modify | ⬜ |
| `.mahabharatha/schemas/archived/task-graph.schema.json` | OFX-005 | Create (archive) | ⬜ |
| `.mahabharatha/task_graph.py` | OFX-005 | Modify | ⬜ |
| `.gitignore` | OFX-005 | Modify | ⬜ |
| `mahabharatha/validation.py` | OFX-006 | Modify | ⬜ |
| `mahabharatha/orchestrator.py` | OFX-007 | Modify | ⬜ |
| `mahabharatha/launcher.py` | OFX-008 | Modify | ⬜ |
| `mahabharatha/parser.py` | OFX-009 | Modify | ⬜ |
| `mahabharatha/commands/design.py` | OFX-010 | Modify | ⬜ |
| `.claude/commands/mahabharatha:kurukshetra.md` | OFX-011 | Modify | ⬜ |
| `.claude/commands/mahabharatha:design.md` | OFX-011 | Modify | ⬜ |
| `tests/integration/test_full_rush_cycle.py` | OFX-012 | Create | ⬜ |

---

## Progress Tracker

```
Last Updated: 2026-01-27

Level 1: ✅✅✅✅ (4/4) - Test Infrastructure
Level 2: ✅✅✅✅ (4/4) - Core Implementation
Level 3: ✅✅ (2/2) - Integration
Level 4: ✅ (1/1) - Documentation
Level 5: ✅ (1/1) - Final Verification

Overall: 12/12 (100%) ✅
```

---

## Parallelization Potential

| Level | Tasks | Sequential | Parallel | Speedup |
|-------|-------|------------|----------|---------|
| 1 | 4 | 120 min | 30 min | 4.0x |
| 2 | 4 | 160 min | 45 min | 3.6x |
| 3 | 2 | 40 min | 20 min | 2.0x |
| 4 | 1 | 15 min | 15 min | 1.0x |
| 5 | 1 | 30 min | 30 min | 1.0x |
| **Total** | **12** | **365 min** | **140 min** | **2.6x** |

---

## Dependency Graph

```
Level 1 (Tests - TDD):
  OFX-001 ─┬─ OFX-002 ─┬─ OFX-003 ─┬─ OFX-004
           │           │           │
Level 2:   ▼           ▼           ▼
  OFX-005   OFX-007    OFX-008
  OFX-006
           │
Level 3:   ▼
  OFX-009 ─┬─ OFX-010
           │
Level 4:   ▼
      OFX-011
           │
Level 5:   ▼
      OFX-012
```

---

## Verification Commands

```bash
# Validate task graph
python -c "from mahabharatha.validation import *; import json; d=json.load(open('.gsd/specs/orchestrator-fixes/task-graph.json')); print(validate_task_graph(d)); print(validate_dependencies(d)); print(validate_file_ownership(d))"

# Dry-run
mahabharatha kurukshetra --feature orchestrator-fixes --dry-run --mode subprocess

# Run all new tests
pytest tests/unit/test_schema_validation.py tests/unit/test_worker_lifecycle.py tests/unit/test_state_sync.py tests/integration/test_orchestrator_fixes.py tests/integration/test_full_rush_cycle.py -v

# Full test suite
pytest tests/ -v --tb=short
```

---

## MAHABHARATHA Kurukshetra Execution

```bash
# Execute with 4 workers
mahabharatha kurukshetra --feature orchestrator-fixes --workers 4 --mode subprocess

# Monitor progress
mahabharatha status --feature orchestrator-fixes
```

---

## Resolved Questions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Archive or delete old schema? | **Archive** to `.mahabharatha/schemas/archived/` + .gitignore | Preserves history, prevents accidental use |
| WorkerTracker class location? | **Top-level class** in orchestrator.py | Easy testing, no import complexity, logical grouping |
| Initialization wait timeout? | **600 seconds** (10 min) | Allows slow container builds, configurable |

---

## Notes

- TDD approach: Level 1 creates tests that initially fail
- Level 2 implements fixes that make tests pass
- Consolidated orchestrator fixes into single task (OFX-007) for file ownership
- Schema consolidation archives old schema instead of deleting
- Backward compatibility maintained with existing DC-012 task graphs
