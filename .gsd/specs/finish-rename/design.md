# Technical Design: finish-rename

## Metadata
- **Feature**: finish-rename
- **Status**: DRAFT
- **Created**: 2026-01-30

## 1. Overview

Finish the troubleshoot→debug rename. Previous work completed all `mahabharatha/` package renames (commands, diagnostics, CLI, tests). Remaining: `.mahabharatha/` runtime scripts, installed commands, documentation.

## 2. Scope

### Already Completed
- `mahabharatha/commands/debug.py` (renamed from troubleshoot.py)
- `mahabharatha/commands/__init__.py`, `mahabharatha/cli.py` (imports updated)
- `mahabharatha/data/commands/mahabharatha:debug.md` (slash command renamed)
- `mahabharatha/diagnostics/` (all refs cleaned)
- `tests/unit/test_debug_cmd.py`, `tests/integration/test_debug.py` (renamed)
- `install_commands.py` (z: shortcut support added)

### Remaining Work (3 levels, 5 tasks)

| Level | Tasks | Parallel |
|-------|-------|----------|
| L1 - Code | 2 tasks: .mahabharatha/ scripts + command reinstall | Yes |
| L2 - Docs | 2 tasks: backlog/coverage docs + .gsd task docs | Yes |
| L3 - Quality | 1 task: gates | No |

## 3. File Ownership

| File | Task | Operation |
|------|------|-----------|
| `.mahabharatha/debug.py` | FR-L1-001 | create (from rename) |
| `.mahabharatha/troubleshoot.py` | FR-L1-001 | delete |
| `.mahabharatha/tests/test_debug.py` | FR-L1-001 | create (from rename) |
| `.mahabharatha/tests/test_troubleshoot.py` | FR-L1-001 | delete |
| `.claude/commands/` | FR-L1-002 | reinstall |
| `mahabharatha/data/commands/mahabharatha:debug.md` | FR-L1-002 | modify (1 line) |
| `tasks/COVERAGE-100-BACKLOG.md` | FR-L2-001 | modify |
| `claudedocs/backlog.md` | FR-L2-001 | modify |
| `.gsd/tasks/prompts/L3-quality-commands.md` | FR-L2-002 | modify |
| `.gsd/tasks/prompts/README.md` | FR-L2-002 | modify |
| `.gsd/tasks/documentation/BACKLOG.md` | FR-L2-002 | modify |
| `.gsd/tasks/cli-commands-tests/BACKLOG.md` | FR-L2-002 | modify |

## 4. Dependency Graph

```
L1: FR-L1-001 (rename .mahabharatha/ scripts) ──┐
    FR-L1-002 (reinstall + fix cmd)   ──┤
                                         │
L2: FR-L2-001 (user docs)             ──┤─ depends on L1
    FR-L2-002 (.gsd task docs)        ──┘
                                         │
L3: FR-L3-001 (quality gates)         ──── depends on L2
```

## 5. Recommended Workers
- Optimal: 2 workers (widest level is 2 tasks)
- Maximum: 2 workers

## 6. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Architecture | | | PENDING |
