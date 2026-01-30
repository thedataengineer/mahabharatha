# Requirements: bug-fix-sweep

**Status**: APPROVED
**Feature**: bug-fix-sweep
**Created**: 2026-01-30

## Summary

Fix 5 pre-existing test failures across 3 root causes.

## Failures

### Bug 1: StateManager TOCTOU race condition (2 tests)
- `test_concurrent_claims` - 5 threads claim same task, multiple succeed
- `test_concurrent_event_appending` - 10 threads append events, some lost

### Bug 2: VerificationExecutor bypasses validation (1 test)
- `test_verify_invalid_command` - `trust_commands=True` skips dangerous pattern checks

### Bug 3: WorkerProtocol tests hang on 120s polling (2 tests)
- `test_start_sets_running_worker_state` - hangs in claim_next_task()
- `test_start_clean_exit_sets_stopped` - hangs in claim_next_task()
