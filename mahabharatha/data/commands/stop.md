# Mahabharatha Stop

Stop Mahabharatha workers gracefully or forcefully.

## Usage

```bash
# Stop all workers gracefully
mahabharatha stop

# Stop specific worker
mahabharatha stop --worker 2

# Force immediate termination
mahabharatha stop --force

# Stop specific feature
mahabharatha stop --feature user-auth
```

## CLI Flags

```
mahabharatha stop [OPTIONS]

Options:
  -f, --feature TEXT     Feature to stop (auto-detected)
  -w, --worker INTEGER   Stop specific worker only
  --force                Force immediate termination (no checkpoint)
  --timeout INTEGER      Graceful shutdown timeout in seconds (default: 30)
```

## Graceful vs Force Stop

### Graceful Stop (Default)

1. Sends checkpoint signal to workers
2. Workers commit any in-progress work (WIP commit)
3. Workers update state with checkpoint info
4. Containers stop cleanly
5. State preserved for resume

```bash
mahabharatha stop
```

### Force Stop (--force)

1. Immediately terminates containers
2. No WIP commits made
3. In-progress tasks marked as failed
4. May lose uncommitted work

```bash
mahabharatha stop --force
```

## Checkpoint Behavior

When stopped gracefully, workers:

1. **Commit WIP**: Creates checkpoint commit with current progress
2. **Update State**: Marks current task as PAUSED
3. **Log Context**: Records where to resume
4. **Clean Exit**: Exits with code 2 (CHECKPOINT)

### WIP Commit Format

```
WIP: Mahabharatha [worker-{id}] checkpoint during {task_id}

Status: {percentage}% complete
Files modified:
  - path/to/file1.py (added)

Worker-ID: {id}
Feature: {feature}
Context-Usage: {percentage}%
```

## Cross-Session Coordination

```bash
FEATURE=${Mahabharatha_FEATURE:-$(cat .gsd/.current-feature 2>/dev/null)}
TASK_LIST=${CLAUDE_CODE_TASK_LIST_ID:-$FEATURE}
```

## Task System Updates

After checkpoint/stop completes, update Claude Code Tasks to reflect stopped state:

**Graceful Stop:**
1. Call TaskList to find all in_progress tasks
2. For each in_progress task, call TaskUpdate:
   - taskId: the task's Claude Task ID
   - description: Append "PAUSED: Graceful stop at {timestamp}. Resume with /mahabharatha:Kurukshetra --resume"
   - (Keep status as "in_progress" — no "paused" status exists in the Task system)

**Force Stop (--force):**
1. Call TaskList to find all in_progress tasks
2. For each in_progress task, call TaskUpdate:
   - taskId: the task's Claude Task ID
   - description: Append "FORCE STOPPED: {timestamp}. Uncommitted work may be lost."
   - (Keep status as "in_progress" — orchestrator will decide next action on resume)

## Recovery After Stop

Resume execution:

```bash
# Resume from checkpoint
mahabharatha Kurukshetra --resume

# Resume with different worker count
mahabharatha Kurukshetra --resume --workers 3
```

Check state:

```bash
# See what was in progress
mahabharatha status

# Check for blocked tasks
mahabharatha status --json | jq '.tasks | map(select(.status == "paused"))'
```

## Stopping Specific Workers

```bash
# Stop only worker 2
mahabharatha stop --worker 2

# Force stop worker 2
mahabharatha stop --worker 2 --force
```

Other workers continue executing.

## Timeout Handling

Default timeout is 30 seconds for graceful shutdown.

```bash
# Wait longer for checkpoint
mahabharatha stop --timeout 60

# Quick timeout
mahabharatha stop --timeout 10
```

If timeout expires, remaining workers are force-stopped.

## State After Stop

| Component | Graceful | Force |
|-----------|----------|-------|
| Containers | Stopped | Killed |
| Worktrees | Preserved | Preserved |
| State file | Updated | May be stale |
| Current tasks | PAUSED | FAILED |
| WIP changes | Committed | Lost |

## Examples

```bash
# Lunch break - stop gracefully
mahabharatha stop

# Emergency - stop immediately
mahabharatha stop --force

# Stop problematic worker
mahabharatha stop --worker 3 --force

# Clean stop with extra time
mahabharatha stop --timeout 60
```

## Integration

After stopping:

```bash
# Check final status
mahabharatha status

# View logs for issues
mahabharatha logs --level error

# Retry failed tasks
mahabharatha retry --all-failed

# Resume execution
mahabharatha Kurukshetra --resume

# Full cleanup
mahabharatha cleanup --feature my-feature
```

## Help

When `--help` is passed in `$ARGUMENTS`, display usage and exit:

```
/mahabharatha:stop — Stop Mahabharatha workers gracefully or forcefully.

Flags:
  -f, --feature TEXT     Feature to stop (auto-detected)
  -w, --worker INTEGER   Stop specific worker only
  --force                Force immediate termination (no checkpoint)
  --timeout INTEGER      Graceful shutdown timeout in seconds (default: 30)
  --help                 Show this help message
```
