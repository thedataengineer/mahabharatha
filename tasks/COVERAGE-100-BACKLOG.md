# ZERG 100% Coverage Task Backlog

**Created**: 2026-01-26
**Status**: IN PROGRESS
**Target**: 100% test coverage (currently 77%)
**Tests**: 1539 passing
**Total Lines Uncovered**: ~1884

---

## Coverage Gap Analysis

### Critical Priority (< 40% coverage) - 477 lines uncovered
| File | Coverage | Lines Missing | Priority |
|------|----------|---------------|----------|
| `zerg/commands/rush.py` | 22% | 94 | **P0** |
| `zerg/commands/merge_cmd.py` | 33% | 96 | **P0** |
| `zerg/commands/retry.py` | 33% | 84 | **P0** |
| `zerg/commands/plan.py` | 38% | 111 | **P0** |
| `zerg/commands/logs.py` | 41% | 92 | **P0** |

### High Priority (40-60% coverage) - 635 lines uncovered
| File | Coverage | Lines Missing | Priority |
|------|----------|---------------|----------|
| `zerg/commands/test_cmd.py` | 48% | 177 | **P1** |
| `zerg/commands/cleanup.py` | 50% | 85 | **P1** |
| `zerg/commands/stop.py` | 52% | 61 | **P1** |
| `zerg/commands/git_cmd.py` | 54% | 120 | **P1** |
| `zerg/commands/init.py` | 57% | 98 | **P1** |
| `zerg/commands/security_rules_cmd.py` | 58% | 25 | **P1** |
| `zerg/commands/status.py` | 60% | 69 | **P1** |

### Medium Priority (60-80% coverage) - 341 lines uncovered
| File | Coverage | Lines Missing | Priority |
|------|----------|---------------|----------|
| `zerg/state.py` | 69% | 105 | **P2** |
| `zerg/commands/build.py` | 72% | 63 | **P2** |
| `zerg/launcher.py` | 75% | 87 | **P2** |
| `zerg/orchestrator.py` | 76% | 86 | **P2** |

### Low Priority (80-95% coverage) - 424 lines uncovered
| File | Coverage | Lines Missing | Priority |
|------|----------|---------------|----------|
| `zerg/containers.py` | 81% | 29 | P3 |
| `zerg/commands/design.py` | 81% | 33 | P3 |
| `zerg/worker_main.py` | 81% | 13 | P3 |
| `zerg/gates.py` | 82% | 17 | P3 |
| `zerg/commands/analyze.py` | 83% | 36 | P3 |
| `zerg/worker_protocol.py` | 83% | 49 | P3 |
| `zerg/validation.py` | 86% | 24 | P3 |
| `zerg/commands/refactor.py` | 87% | 34 | P3 |
| `zerg/worktree.py` | 87% | 16 | P3 |
| `zerg/charter.py` | 88% | 13 | P3 |
| `zerg/security_rules.py` | 89% | 22 | P3 |
| `zerg/assign.py` | 91% | 9 | P3 |
| `zerg/config.py` | 91% | 7 | P3 |
| `zerg/git_ops.py` | 91% | 14 | P3 |
| `zerg/commands/review.py` | 91% | 24 | P3 |
| `zerg/commands/debug.py` | 92% | 21 | P3 |
| Others (93-98%) | 93-98% | ~43 | P4 |

### Zero Coverage - 7 lines
| File | Coverage | Lines Missing | Priority |
|------|----------|---------------|----------|
| `zerg/__main__.py` | 0% | 3 | P3 |
| `zerg/schemas/__init__.py` | 0% | 4 | P3 |

---

## Task Backlog by Level

### Level 0: Test Infrastructure (Parallel: 3 tasks)
Foundation for all other test work.

| ID | Description | Files Owned | Deps | Verification |
|----|-------------|-------------|------|--------------|
| **COV-L0-001** | Create test utilities for command mocking | `tests/helpers/command_mocks.py` | - | `pytest tests/helpers/ -v` |
| **COV-L0-002** | Create test fixtures for state/orchestrator | `tests/fixtures/state_fixtures.py` | - | `pytest tests/fixtures/ -v` |
| **COV-L0-003** | Create async test helpers | `tests/helpers/async_helpers.py` | - | `pytest tests/helpers/ -v` |

### Level 1: Critical Commands - Tests First (Parallel: 5 tasks)
Target: rush.py, merge_cmd.py, retry.py, plan.py, logs.py

| ID | Description | Files Owned | Deps | Verification |
|----|-------------|-------------|------|--------------|
| **COV-L1-001** | Tests for rush.py (94 lines) | `tests/unit/test_rush_cmd.py` | L0-* | `pytest tests/unit/test_rush_cmd.py -v --cov=zerg/commands/rush` |
| **COV-L1-002** | Tests for merge_cmd.py (96 lines) | `tests/unit/test_merge_cmd.py` | L0-* | `pytest tests/unit/test_merge_cmd.py -v --cov=zerg/commands/merge_cmd` |
| **COV-L1-003** | Tests for retry.py (84 lines) | `tests/unit/test_retry_cmd.py` | L0-* | `pytest tests/unit/test_retry_cmd.py -v --cov=zerg/commands/retry` |
| **COV-L1-004** | Tests for plan.py (111 lines) | `tests/unit/test_plan_cmd.py` | L0-* | `pytest tests/unit/test_plan_cmd.py -v --cov=zerg/commands/plan` |
| **COV-L1-005** | Tests for logs.py (92 lines) | `tests/unit/test_logs_cmd.py` | L0-* | `pytest tests/unit/test_logs_cmd.py -v --cov=zerg/commands/logs` |

### Level 2: High Priority Commands - Tests First (Parallel: 7 tasks)
Target: test_cmd.py, cleanup.py, stop.py, git_cmd.py, init.py, security_rules_cmd.py, status.py

| ID | Description | Files Owned | Deps | Verification |
|----|-------------|-------------|------|--------------|
| **COV-L2-001** | Tests for test_cmd.py (177 lines) | `tests/unit/test_test_cmd_full.py` | L0-* | `pytest tests/unit/test_test_cmd_full.py -v --cov=zerg/commands/test_cmd` |
| **COV-L2-002** | Tests for cleanup.py (85 lines) | `tests/unit/test_cleanup_cmd.py` | L0-* | `pytest tests/unit/test_cleanup_cmd.py -v --cov=zerg/commands/cleanup` |
| **COV-L2-003** | Tests for stop.py (61 lines) | `tests/unit/test_stop_cmd.py` | L0-* | `pytest tests/unit/test_stop_cmd.py -v --cov=zerg/commands/stop` |
| **COV-L2-004** | Tests for git_cmd.py (120 lines) | `tests/unit/test_git_cmd_full.py` | L0-* | `pytest tests/unit/test_git_cmd_full.py -v --cov=zerg/commands/git_cmd` |
| **COV-L2-005** | Tests for init.py (98 lines) | `tests/unit/test_init_cmd.py` | L0-* | `pytest tests/unit/test_init_cmd.py -v --cov=zerg/commands/init` |
| **COV-L2-006** | Tests for security_rules_cmd.py (25 lines) | `tests/unit/test_security_rules_cmd.py` | L0-* | `pytest tests/unit/test_security_rules_cmd.py -v --cov=zerg/commands/security_rules_cmd` |
| **COV-L2-007** | Tests for status.py (69 lines) | `tests/unit/test_status_cmd.py` | L0-* | `pytest tests/unit/test_status_cmd.py -v --cov=zerg/commands/status` |

### Level 3: Core Infrastructure - Tests First (Parallel: 4 tasks)
Target: state.py, build.py, launcher.py, orchestrator.py

| ID | Description | Files Owned | Deps | Verification |
|----|-------------|-------------|------|--------------|
| **COV-L3-001** | Tests for state.py (105 lines) | `tests/unit/test_state_full.py` | L0-* | `pytest tests/unit/test_state_full.py -v --cov=zerg/state` |
| **COV-L3-002** | Tests for build.py (63 lines) | `tests/unit/test_build_cmd.py` | L0-* | `pytest tests/unit/test_build_cmd.py -v --cov=zerg/commands/build` |
| **COV-L3-003** | Tests for launcher.py (87 lines) | `tests/unit/test_launcher_full.py` | L0-* | `pytest tests/unit/test_launcher_full.py -v --cov=zerg/launcher` |
| **COV-L3-004** | Tests for orchestrator.py (86 lines) | `tests/unit/test_orchestrator_full.py` | L0-* | `pytest tests/unit/test_orchestrator_full.py -v --cov=zerg/orchestrator` |

### Level 4: Supporting Modules - Tests First (Parallel: 8 tasks)
Target: Remaining 80-90% coverage files

| ID | Description | Files Owned | Deps | Verification |
|----|-------------|-------------|------|--------------|
| **COV-L4-001** | Tests for containers.py (29 lines) | `tests/unit/test_containers_full.py` | L0-* | `pytest tests/unit/test_containers_full.py -v --cov=zerg/containers` |
| **COV-L4-002** | Tests for design.py (33 lines) | `tests/unit/test_design_cmd_full.py` | L0-* | `pytest tests/unit/test_design_cmd_full.py -v --cov=zerg/commands/design` |
| **COV-L4-003** | Tests for worker_main.py (13 lines) | `tests/unit/test_worker_main.py` | L0-* | `pytest tests/unit/test_worker_main.py -v --cov=zerg/worker_main` |
| **COV-L4-004** | Tests for gates.py (17 lines) | `tests/unit/test_gates_full.py` | L0-* | `pytest tests/unit/test_gates_full.py -v --cov=zerg/gates` |
| **COV-L4-005** | Tests for analyze.py (36 lines) | `tests/unit/test_analyze_cmd_full.py` | L0-* | `pytest tests/unit/test_analyze_cmd_full.py -v --cov=zerg/commands/analyze` |
| **COV-L4-006** | Tests for worker_protocol.py (49 lines) | `tests/unit/test_worker_protocol_full.py` | L0-* | `pytest tests/unit/test_worker_protocol_full.py -v --cov=zerg/worker_protocol` |
| **COV-L4-007** | Tests for validation.py (24 lines) | `tests/unit/test_validation_full.py` | L0-* | `pytest tests/unit/test_validation_full.py -v --cov=zerg/validation` |
| **COV-L4-008** | Tests for refactor.py (34 lines) | `tests/unit/test_refactor_cmd_full.py` | L0-* | `pytest tests/unit/test_refactor_cmd_full.py -v --cov=zerg/commands/refactor` |

### Level 5: Final Coverage - Tests First (Parallel: 10 tasks)
Target: All remaining files to 100%

| ID | Description | Files Owned | Deps | Verification |
|----|-------------|-------------|------|--------------|
| **COV-L5-001** | Tests for worktree.py (16 lines) | `tests/unit/test_worktree_full.py` | L0-* | `pytest tests/unit/test_worktree_full.py -v --cov=zerg/worktree` |
| **COV-L5-002** | Tests for charter.py (13 lines) | `tests/unit/test_charter_full.py` | L0-* | `pytest tests/unit/test_charter_full.py -v --cov=zerg/charter` |
| **COV-L5-003** | Tests for security_rules.py (22 lines) | `tests/unit/test_security_rules_full.py` | L0-* | `pytest tests/unit/test_security_rules_full.py -v --cov=zerg/security_rules` |
| **COV-L5-004** | Tests for assign.py, config.py, git_ops.py | `tests/unit/test_core_utils_full.py` | L0-* | `pytest tests/unit/test_core_utils_full.py -v` |
| **COV-L5-005** | Tests for review.py (24 lines) | `tests/unit/test_review_cmd_full.py` | L0-* | `pytest tests/unit/test_review_cmd_full.py -v --cov=zerg/commands/review` |
| **COV-L5-006** | Tests for debug.py (21 lines) | `tests/unit/test_debug_full.py` | L0-* | `pytest tests/unit/test_debug_full.py -v --cov=zerg/commands/debug` |
| **COV-L5-007** | Tests for __main__.py (3 lines) | `tests/unit/test_main_entry.py` | L0-* | `pytest tests/unit/test_main_entry.py -v --cov=zerg/__main__` |
| **COV-L5-008** | Tests for schemas/__init__.py (4 lines) | `tests/unit/test_schemas.py` | L0-* | `pytest tests/unit/test_schemas.py -v --cov=zerg/schemas` |
| **COV-L5-009** | Tests for remaining 93-98% files | `tests/unit/test_final_coverage.py` | L0-* | `pytest tests/unit/test_final_coverage.py -v` |
| **COV-L5-010** | Integration coverage validation | `tests/integration/test_full_coverage.py` | L1-L5 | `pytest --cov=zerg --cov-fail-under=100` |

### Level 6: Documentation & Skills Update (Parallel: 2 tasks)
Update dependencies affected by any refactoring.

| ID | Description | Files Owned | Deps | Verification |
|----|-------------|-------------|------|--------------|
| **COV-L6-001** | Update skills for new test patterns | `skills/sc:test.md` | L5-* | `test -f skills/sc:test.md` |
| **COV-L6-002** | Update CLAUDE.md with test guidelines | `CLAUDE.md` (test section) | L5-* | `grep -q "100% coverage" CLAUDE.md` |

---

## Critical Path

```
L0-001 ─┬─→ L1-001 (rush) ────────┐
L0-002 ─┼─→ L1-002 (merge) ───────┤
L0-003 ─┼─→ L1-003 (retry) ───────┤
        ├─→ L1-004 (plan) ────────┼─→ L2-* (7 parallel) ─→ L3-* (4 parallel)
        └─→ L1-005 (logs) ────────┘
                                              │
                                              ↓
                              L4-* (8 parallel) ─→ L5-* (10 parallel)
                                              │
                                              ↓
                                        L5-010 (validation)
                                              │
                                              ↓
                                        L6-* (docs/skills)
```

**Critical Path Tasks**: L0-001 → L1-001 → L5-010 (rush.py has most impact)

---

## Execution Summary

| Level | Tasks | Parallel Workers | Est. Focus |
|-------|-------|------------------|------------|
| L0 | 3 | 3 | Test infrastructure |
| L1 | 5 | 5 | Critical commands (22-41% coverage) |
| L2 | 7 | 5 | High priority commands (48-60% coverage) |
| L3 | 4 | 4 | Core infrastructure (69-76% coverage) |
| L4 | 8 | 5 | Supporting modules (81-87% coverage) |
| L5 | 10 | 5 | Final coverage + validation |
| L6 | 2 | 2 | Documentation updates |

**Total Tasks**: 39
**Max Parallelization**: 5 workers
**Estimated Sessions**: 6-7 (with 5 parallel workers)

---

## Progress Tracking

| Level | Status | Completed | Total | % | Claude Task IDs |
|-------|--------|-----------|-------|---|-----------------|
| L0 | PENDING | 0 | 3 | 0% | #1, #2, #3 |
| L1 | PENDING | 0 | 5 | 0% | #4, #5, #6, #7, #8 |
| L2 | PENDING | 0 | 7 | 0% | #9, #10, #11, #12, #13, #14, #15 |
| L3 | PENDING | 0 | 4 | 0% | #16, #17, #18, #19 |
| L4 | PENDING | 0 | 4 | 0% | #20, #21, #22, #23 |
| L5 | PENDING | 0 | 5 | 0% | #24, #25, #26, #27, #28 |
| L6 | PENDING | 0 | 1 | 0% | #29 |
| **TOTAL** | **PENDING** | **0** | **29** | **0%** |

---

## Verification Commands

```bash
# Run all tests with coverage
pytest --cov=zerg --cov-report=term-missing

# Verify 100% coverage
pytest --cov=zerg --cov-fail-under=100

# Run specific level tests
pytest tests/unit/test_rush_cmd.py tests/unit/test_merge_cmd.py -v

# Generate HTML report
pytest --cov=zerg --cov-report=html
```

---

## Blockers & Notes

- **Deprecation Warning**: `datetime.utcnow()` in `zerg/logging.py:28` - fix during L5
- **Async Testing**: Some commands require async test patterns (L0-003)
- **Mocking Strategy**: Commands with subprocess calls need careful mocking

---

*Last Updated: 2026-01-26*
