# /mahabharatha:status

Display current execution status and progress.

## Synopsis

```
/mahabharatha:status [OPTIONS]
```

## Description

`/mahabharatha:status` produces a snapshot of the current MAHABHARATHA execution state, including feature name, phase, orchestrator status, elapsed time, and per-level progress bars.

### Data Sources

The command uses two data sources:

1. **Claude Code Task system** (primary) -- Retrieves task statuses via `TaskList`. This is the authoritative source of truth.
2. **State JSON** (supplementary) -- Reads `.mahabharatha/state/<feature>.json` for worker assignment details not stored in the Task system.

If the two sources disagree, the Task system takes precedence. Mismatches are flagged in the output.

### Phases

The status report shows the current phase of the feature:

| Phase | Description |
|-------|-------------|
| PLANNING | Requirements gathering in progress |
| DESIGNING | Architecture and task graph generation |
| EXECUTING | Workers actively running tasks |
| MERGING | Level merge in progress |
| COMPLETE | All tasks finished |

## Options

| Option | Description |
|--------|-------------|
| `--tasks` | Show detailed per-task status with individual task states |
| `--dashboard` | Launch live TUI dashboard (requires separate terminal) |
| `--watch` | Auto-refresh text-based status display |
| `--interval N` | Refresh interval in seconds for `--watch` mode (default: 5) |
| `--json` | Output status as JSON for scripting |

## Examples

```bash
# One-shot status check
/mahabharatha:status

# Detailed task list
/mahabharatha:status --tasks

# Live TUI dashboard (run in a separate terminal during kurukshetra)
/mahabharatha:status --dashboard

# Auto-refreshing text output
/mahabharatha:status --watch --interval 2

# JSON output for scripting
/mahabharatha:status --json
```

## Output

A typical status report:

```
======================================================================
                         FACTORY STATUS
======================================================================

Feature:      user-auth
Phase:        EXECUTING
Orchestrator: Running (PID: 12345)
Started:      2026-01-28T10:30:00Z
Elapsed:      00:15:32

----------------------------------------------------------------------
                              PROGRESS
----------------------------------------------------------------------

Task System: 8/12 tasks (2 pending, 2 active)
Overall: [=============>        ] 67% (8/12 tasks)

Level 1 (Foundation):   [====================] Complete (3/3 tasks)
Level 2 (Core):         [=============>      ] In Progress (3/4 tasks)
Level 3 (Integration):  [                    ] Pending (0/3 tasks)
Level 4 (Testing):      [                    ] Pending (0/2 tasks)

======================================================================

Commands:
  /mahabharatha:logs {N}      View logs from worker N
  /mahabharatha:stop          Stop all workers
  /mahabharatha:retry {ID}    Retry a failed task

======================================================================
```

## Worker Intelligence Panel

When worker intelligence is active (workers are running with heartbeat monitoring), the status output includes an additional section:

```
----------------------------------------------------------------------
                        WORKER INTELLIGENCE
----------------------------------------------------------------------

Heartbeats:
  Worker 0: ✅ alive (3s ago) — TASK-003 verifying_tier2 65%
  Worker 1: ✅ alive (1s ago) — TASK-004 implementing 30%
  Worker 2: ⚠️ stalled (145s ago) — TASK-005 implementing 10%

Escalations:
  ⚠ Worker 1 | TASK-004 | ambiguous_spec
    "Spec says 'handle auth errors' but doesn't define error types"

Progress:
  Worker 0: 2/5 tasks ████░░░░░░ 40%  [tier1 ✅ tier2 🔄]
  Worker 1: 1/5 tasks ██░░░░░░░░ 20%  [tier1 ✅]
  Worker 2: 0/5 tasks ░░░░░░░░░░  0%  [stalled]
```

### Data Sources

The Worker Intelligence panel reads from:

| File | Content |
|------|---------|
| `.mahabharatha/state/heartbeat-{id}.json` | Per-worker heartbeat with task, step, and progress |
| `.mahabharatha/state/progress-{id}.json` | Tasks completed/total, current step, tier results |
| `.mahabharatha/state/escalations.json` | Unresolved escalations from workers |

### Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `heartbeat.stall_timeout_seconds` | 120 | Seconds before a worker is marked stalled |
| `escalation.auto_interrupt` | true | Print escalation alerts to terminal |
| `escalation.poll_interval_seconds` | 5 | How often the orchestrator checks for escalations |

## See Also

- [[mahabharatha-kurukshetra]] -- Starts the execution that status monitors
- [[mahabharatha-logs]] -- Detailed worker and task logs
- [[mahabharatha-stop]] -- Stop execution
- [[mahabharatha-Reference]] -- Full command index
