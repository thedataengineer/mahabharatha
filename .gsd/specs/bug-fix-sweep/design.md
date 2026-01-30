# Technical Design: bug-fix-sweep

**Status**: DRAFT
**Created**: 2026-01-30

## 1. Overview

Fix 5 pre-existing test failures across 3 root causes: StateManager threading race condition, VerificationExecutor skipping dangerous command validation, and WorkerProtocol tests hanging on 120s polling timeout.

## 2. Bug Fixes

### BF-L1-001: StateManager thread safety
**File**: `zerg/state.py`
**Root cause**: `_atomic_update()` releases `self._lock` (RLock) before `yield` at line 88. Multiple threads on a shared StateManager instance bypass the lock and operate on stale in-memory state concurrently.

**Fix**: Hold `self._lock` for the entire yield duration in the outermost `_atomic_update` context. Move the `yield` INSIDE the `with self._lock:` block so threads are serialized.

```python
# BEFORE (broken):
with self._lock:
    # reload state
yield  # ← Lock released, threads race here
self._raw_save()

# AFTER (fixed):
with self._lock:
    # reload state
    yield  # ← Lock held, threads serialized
    self._raw_save()
```

### BF-L1-002: VerificationExecutor always check dangerous patterns
**File**: `zerg/verify.py`
**Root cause**: `_get_executor()` hardcodes `trust_commands=True` at line 63, which skips the dangerous pattern check in `CommandExecutor.validate_command()`.

**Fix**: Change to `trust_commands=False`. Verification commands should still be validated for dangerous patterns (`;`, `rm -rf`, etc). The `allow_unlisted=True` already permits custom commands.

### BF-L1-003: WorkerProtocol tests mock claim_next_task
**File**: `tests/unit/test_worker_lifecycle.py`
**Root cause**: Tests call `protocol.start()` which calls `claim_next_task(max_wait=120)`. With mocked empty task lists, it polls for 120 seconds, exceeding test timeout.

**Fix**: Patch `claim_next_task` on the protocol instance to return `None` immediately, or patch `time.sleep` and `time.time` to accelerate the polling. The cleanest approach is to mock `claim_next_task` directly since the tests are verifying state writes, not claim behavior.

## 3. File Ownership

| File | Task | Operation |
|------|------|-----------|
| `zerg/state.py` | BF-L1-001 | modify |
| `zerg/verify.py` | BF-L1-002 | modify |
| `tests/unit/test_worker_lifecycle.py` | BF-L1-003 | modify |
| `tests/unit/test_state_extended.py` | BF-L1-001 | read (verify) |
| `tests/unit/test_verify.py` | BF-L1-002 | read (verify) |

## 4. Verification

Each task runs its specific test file to confirm the fix:
- BF-L1-001: `python -m pytest tests/unit/test_state_extended.py::TestConcurrency -xvs`
- BF-L1-002: `python -m pytest tests/unit/test_verify.py::TestVerificationExecutor::test_verify_invalid_command -xvs`
- BF-L1-003: `python -m pytest tests/unit/test_worker_lifecycle.py::TestWorkerLifecycle::test_start_sets_running_worker_state tests/unit/test_worker_lifecycle.py::TestWorkerLifecycle::test_start_clean_exit_sets_stopped -xvs --timeout=15`

## 5. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| RLock scope change breaks existing callers | Low - nested calls still work via _file_lock_depth | Verify all state tests pass |
| trust_commands=False breaks real verification | Low - allow_unlisted=True still permits custom cmds | Run full verify test suite |
| Mock changes miss real start() behavior | Low - tests are about state writes, not claim logic | Keep claim_next_task behavior tested elsewhere |
