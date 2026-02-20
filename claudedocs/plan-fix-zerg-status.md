# Plan: Fix /mahabharatha:status to Show Active Worker Progress

**Created**: 2026-01-26
**Status**: Pending implementation

## Problem

- Worker protocol specifies state files (line 346-349 of mahabharatha:worker.md) but they aren't written
- `/mahabharatha:status` doesn't read from state files
- Orchestrator only saves checkpoint on stop, not during execution
- No way to see Task agents, Docker containers, or subprocess workers from another session

## Root Cause

The communication channels are documented but not implemented:
```
1. .mahabharatha/state/{feature}.json - shared task state (NOT WRITTEN)
2. .gsd/specs/{feature}/progress.md - progress log (PARTIAL)
3. .mahabharatha/logs/worker-{id}.log - worker output (NOT WRITTEN)
```

## Solution: Implement Documented IPC Protocol

### Files to Modify

| File | Change |
|------|--------|
| `.mahabharatha/state.py` | Add `WorkerHeartbeat` class, `StateManager.update_worker()` |
| `.mahabharatha/status.py` | Add `StatusLoader.load_from_files()` to read state |
| `.mahabharatha/orchestrator.py` | Call `state.save()` after each worker update |
| `.claude/commands/mahabharatha:worker.md` | Add heartbeat write instructions |
| `.claude/commands/mahabharatha:status.md` | Read from state files |

### State File Structure (Per Worker Protocol)
```
.mahabharatha/
  state.json                    # ExecutionState (feature, level, tasks)
  state/{feature}.json          # Feature-specific state
  logs/
    worker-0.log
    worker-1.log
    orchestrator.log
```

### Implementation Details

#### 1. StateManager Updates (state.py)

Add continuous state updates during execution:

```python
def update_task_status(self, task_id: str, status: TaskStatus, worker_id: str = None):
    """Update task status and persist to disk."""
    self.tasks[task_id].status = status
    self.tasks[task_id].worker_id = worker_id
    self.save()  # Atomic write

def update_worker_heartbeat(self, worker_id: str, task_id: str, step: str):
    """Record worker heartbeat."""
    self.workers[worker_id] = WorkerState(
        id=worker_id, status="running", current_task=task_id
    )
    self.save()
```

#### 2. StatusLoader (status.py)

Add file-based state loading:

```python
def load_status(feature: str = None) -> Dashboard:
    """Load status from state files."""
    # 1. Try .mahabharatha/state.json
    state = ExecutionState.load()
    if state:
        return _state_to_dashboard(state)

    # 2. Try feature-specific state
    if feature:
        state = ExecutionState.load(f".mahabharatha/state/{feature}.json")
        if state:
            return _state_to_dashboard(state)

    # 3. Fall back to PROGRESS.md parsing
    return _parse_progress_md()
```

#### 3. Worker Heartbeat Instructions (mahabharatha:worker.md)

Add to Step 4.3 (Implement Task):

```bash
# Write heartbeat before starting task
echo '{"worker_id":"'$WORKER_ID'","task_id":"'$TASK_ID'","status":"running","step":"implementing","updated_at":"'$(date -Iseconds)'"}' > .mahabharatha/heartbeat-$WORKER_ID.json

# Python workers use:
from .mahabharatha.state import ExecutionState
state = ExecutionState.load() or ExecutionState.create(feature)
state.update_task_status(task_id, TaskStatus.RUNNING, worker_id)
```

#### 4. Status Skill Update (mahabharatha:status.md)

Replace manual PROGRESS.md reading with:

```python
from .mahabharatha.status import StatusLoader
dashboard = StatusLoader.load_status(feature)
print(StatusCommand().format_dashboard(dashboard))
```

### Critical Files

- `.mahabharatha/state.py:173-188` - `ExecutionState.save()` (atomic write exists)
- `.mahabharatha/status.py:166` - `StatusCommand` class (needs loader)
- `.mahabharatha/orchestrator.py:237` - `save_checkpoint()` (needs continuous calls)
- `.claude/commands/mahabharatha:worker.md:346-349` - Communication channels spec

### Verification

1. Start `/mahabharatha:kurukshetra` in session A
2. Workers write to `.mahabharatha/state.json` on task start/complete
3. Run `/mahabharatha:status` in session B
4. Verify live worker status appears

### Edge Cases

- Multiple features running: use feature-specific state files
- Stale heartbeats: show "last seen X seconds ago" if >30s old
- Orphaned workers: detect via heartbeat timeout
