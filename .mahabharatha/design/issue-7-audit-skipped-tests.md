# Design: Issue #7 — Audit Skipped Tests

## Inventory

4 skip instances across 3 files:

| # | File | Line | Type | Reason |
|---|------|------|------|--------|
| 1 | `tests/unit/test_state_persistence.py` | 170 | `@pytest.mark.skipif` | Permission tests unreliable on Windows |
| 2 | `tests/unit/test_state_persistence.py` | 190 | `@pytest.mark.skipif` | Permission tests unreliable on Windows |
| 3 | `tests/integration/test_state_integration.py` | 811 | `pytest.skip()` inline | File permission tests not applicable on Windows |
| 4 | `tests/e2e/test_real_execution.py` | 53 | `@pytest.mark.skip` (unconditional) | Requires Claude CLI |

## Assessment

**#1, #2 — Already correct.** Conditional `skipif` with `os.name == "nt"`, documented reason. No action needed.

**#3 — Minor fix.** Uses inline `pytest.skip()` instead of `@pytest.mark.skipif`. Functionally identical but inconsistent with #1/#2. Convert to `@pytest.mark.skipif` decorator for consistency.

**#4 — The real problem.** Unconditional `@pytest.mark.skip` on the entire `TestRealExecution` class. The file already has a working conditional `requires_real_auth` marker (line 47-50) that detects CLI/API key availability. The class-level unconditional skip makes `requires_real_auth` dead code — tests never run even when auth IS available. Fix: remove the unconditional skip; the per-method `@requires_real_auth` decorators already handle conditional skipping.

## Task Graph

### Level 1 (parallel, independent files)

**Task 1**: `tests/e2e/test_real_execution.py`
- Remove `@pytest.mark.skip(reason="Requires Claude CLI")` from line 53
- The `@requires_real_auth` decorator on each method already handles skipping
- Files: `tests/e2e/test_real_execution.py`
- Verify: `python -m pytest tests/e2e/test_real_execution.py --collect-only` (should collect, not skip at class level)

**Task 2**: `tests/integration/test_state_integration.py`
- Convert inline `pytest.skip()` at line 811 to `@pytest.mark.skipif(os.name == "nt", reason="...")` decorator
- Ensures consistency with unit test skip style
- Files: `tests/integration/test_state_integration.py`
- Verify: `python -m pytest tests/integration/test_state_integration.py::TestBackupRestore::test_backup_preserves_file_permissions -v`

### Level 2 (depends on Level 1)

**Task 3**: Run full test suite to confirm no regressions
- Verify: `python -m pytest tests/ -v --tb=short`

## Unresolved Questions

None — scope is small and well-defined.
