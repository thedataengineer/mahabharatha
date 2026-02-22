# /mahabharatha:stop

Stop MAHABHARATHA workers gracefully or forcefully.

## Synopsis

```
/mahabharatha:stop [OPTIONS]
```

## Description

`/mahabharatha:stop` halts running MAHABHARATHA workers. By default it performs a graceful shutdown that allows workers to checkpoint their progress. With `--force`, it terminates workers immediately.

### Graceful Stop (Default)

1. Sends a checkpoint signal to all active workers.
2. Workers create a WIP (work-in-progress) commit with their current changes.
3. Workers update state with checkpoint information.
4. Containers stop cleanly.
5. State is preserved for later resume with `/mahabharatha:kurukshetra --resume`.

In-progress tasks are annotated with `PAUSED` in the Claude Code Task system.

### Force Stop

1. Immediately terminates worker containers.
2. No WIP commits are made.
3. In-progress tasks are marked as failed.
4. Uncommitted work may be lost.

In-progress tasks are annotated with `FORCE STOPPED` in the Claude Code Task system.

### WIP Commit Format

When stopped gracefully, each worker creates a commit with this format:

```
WIP: MAHABHARATHA [worker-<id>] checkpoint during <task_id>

Status: <percentage>% complete
Files modified:
  - path/to/file.py (added)

Worker-ID: <id>
Feature: <feature>
Context-Usage: <percentage>%
```

### State After Stop

| Component | Graceful | Force |
|-----------|----------|-------|
| Containers | Stopped cleanly | Killed |
| Worktrees | Preserved | Preserved |
| State file | Updated | May be stale |
| Current tasks | PAUSED | FAILED |
| WIP changes | Committed | Lost |

## Options

| Option | Description |
|--------|-------------|
| `-f`, `--feature TEXT` | Feature to stop (auto-detected from `.gsd/.current-feature`) |
| `-w`, `--worker INTEGER` | Stop only a specific worker by ID |
| `--force` | Force immediate termination without checkpointing |
| `--timeout INTEGER` | Graceful shutdown timeout in seconds (default: 30) |

## Examples

```bash
# Graceful stop of all workers
/mahabharatha:stop

# Force stop all workers immediately
/mahabharatha:stop --force

# Stop only worker 2
/mahabharatha:stop --worker 2

# Force stop a specific worker
/mahabharatha:stop --worker 3 --force

# Graceful stop with extended timeout
/mahabharatha:stop --timeout 60

# Quick timeout
/mahabharatha:stop --timeout 10
```

## Recovery After Stop

```bash
# Resume execution from checkpoint
/mahabharatha:kurukshetra --resume

# Resume with a different worker count
/mahabharatha:kurukshetra --resume --workers 3

# Check what was in progress
/mahabharatha:status

# View errors before resuming
/mahabharatha:logs --level error

# Retry failed tasks
/mahabharatha:retry --all-failed
```

## See Also

- [[mahabharatha-kurukshetra]] -- Resume execution after stopping
- [[mahabharatha-status]] -- Check state after stop
- [[mahabharatha-retry]] -- Re-run tasks that failed during stop
- [[mahabharatha-logs]] -- Inspect worker logs for issues
- [[mahabharatha-Reference]] -- Full command index
