# Technical Design: align-state-paths

## Metadata
- **Feature**: align-state-paths
- **Status**: DRAFT
- **Created**: 2026-01-31
- **Author**: ZERG Design Mode

---

## 1. Overview

### 1.1 Summary
Align both orchestrators (v2 `.zerg/orchestrator.py` and CLI `zerg/orchestrator.py`) to write state to `.zerg/state/{feature}.json`. Currently the v2 orchestrator writes to `.zerg/state.json` (flat), causing `zerg status` to miss v2 state entirely. Also add a `__main__` entrypoint to the v2 orchestrator and ensure CLI orchestrator persists state immediately after `load()`.

### 1.2 Goals
- Both orchestrators write to `.zerg/state/{feature}.json`
- `zerg status` can read state from either orchestrator
- v2 orchestrator is callable via `python3 .zerg/orchestrator.py --feature X`

### 1.3 Non-Goals
- Rewriting the orchestrator architecture
- Migrating existing `.zerg/state.json` files
- Changing the state file schema

---

## 2. Architecture

```
                    +----------------------+
                    |  /zerg:rush (slash)   |
                    |  zerg rush  (CLI)     |
                    +-------+--------------+
                            |
              +-------------+-------------+
              v                           v
   .zerg/orchestrator.py          zerg/orchestrator.py
   (v2, script mode)              (CLI, library mode)
              |                           |
              |  +---------------------+  |
              +->|  .zerg/state/       |<-+
                 |  {feature}.json     |   <-- ALIGNED
                 +---------+-----------+
                           |
                           v
                    zerg status --dashboard
```

---

## 3. Detailed Design

### 3.1 TASK-001: v2 orchestrator state path alignment

**File**: `.zerg/orchestrator.py`

Changes to `__init__`:
- Add `feature` parameter (default: `"default"`)
- Change `_state_path` from `.zerg/state.json` to `.zerg/state/{feature}.json`

Add `if __name__ == "__main__":` block with argparse:
- `--feature` (required)
- `--workers` (default: 5)
- `--config` (default: `.zerg/config.yaml`)
- `--task-graph` (required)
- `--assignments` (optional)

### 3.2 TASK-002: CLI orchestrator early state persist

**File**: `zerg/orchestrator.py`

Add `self.state.save()` immediately after `self.state.load()` in `start()` method (line ~418). This ensures the state file exists on disk before any work begins, so `zerg status` always finds it.

### 3.3 TASK-003: Slash command feature passthrough

**File**: `zerg/data/commands/zerg:rush.core.md`

The slash command already passes `--feature "$FEATURE"` to the v2 orchestrator. Needs addition of `--task-graph` arg to match the new `__main__` entrypoint.

---

## 4. Key Decisions

### Decision: Default feature name for backward compatibility

**Context**: v2 orchestrator currently has no feature concept.

**Options**:
1. Make `--feature` required everywhere: Breaking change for any direct callers.
2. Default to `"default"`: Backward compatible, state goes to `.zerg/state/default.json`.

**Decision**: Option 2 - default parameter `feature="default"`.

**Rationale**: Preserves backward compatibility while enabling feature-scoped state.

---

## 5. Implementation Plan

### 5.1 Phase Summary

| Phase | Tasks | Parallel |
|-------|-------|----------|
| Foundation (L1) | TASK-001, TASK-002 | Yes |
| Integration (L2) | TASK-003 | No (depends on TASK-001) |

### 5.2 File Ownership

| File | Task ID | Operation |
|------|---------|-----------|
| `.zerg/orchestrator.py` | TASK-001 | modify |
| `zerg/orchestrator.py` | TASK-002 | modify |
| `zerg/data/commands/zerg:rush.core.md` | TASK-003 | modify |

### 5.3 Dependency Graph

```
TASK-001 (v2 state path)  ----+
                               +--> TASK-003 (slash command update)
TASK-002 (CLI early persist)  (independent)
```

---

## 6. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| v2 orchestrator callers pass no feature | Low | Low | Default param `feature="default"` |
| Existing `.zerg/state.json` orphaned | Low | None | Old file can be deleted manually |
| `__main__` block missing task-graph path | Med | Med | Add `--task-graph` arg to argparse |

---

## 7. Testing Strategy

### 7.1 Unit Tests
- v2 orchestrator: `python -m pytest .zerg/tests/test_orchestrator.py -x -q`
- CLI orchestrator: `python -m pytest tests/unit/test_orchestrator.py tests/unit/test_orchestrator_recovery.py -x -q`

### 7.2 Verification
```bash
python -m pytest tests/ -x -q
python -m pytest .zerg/tests/test_orchestrator.py -x -q
```

---

## 8. Parallel Execution Notes

- Minimum: 1 worker (sequential)
- Optimal: 2 workers (TASK-001 + TASK-002 in parallel at L1)
- Maximum: 2 workers (L2 has only 1 task)

---

## 9. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Architecture | | | PENDING |
