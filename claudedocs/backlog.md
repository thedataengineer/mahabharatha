# ZERG Development Backlog

**Updated**: 2026-01-28

## Completed

| # | Item | Completed | Commit |
|---|------|-----------|--------|
| 1 | State file IPC: Workers write WorkerState, orchestrator reloads in poll loop | 2026-01-28 | a189fc7 |

## Backlog

| # | Area | Description | Effort | Status |
|---|------|-------------|--------|--------|
| 2 | Container execution | Workers run as subprocesses only. Docker image never built, ContainerLauncher untested E2E. Plan exists in `claudedocs/plan-container-dogfooding.md` | Medium-Large | Planned |
| 3 | Test coverage (P0 files) | `rush.py` at 22%, `merge_cmd.py` 33%, `retry.py` 33%, `plan.py` 38%. Coverage-100 feature paused at Level 1 | Medium | Paused |
| 4 | Debug cleanup | 10+ debug prints in `troubleshoot.py` should be conditional on `--verbose` | Small | Open |
| 5 | Production dogfooding | Never tested against a real feature build end-to-end | Large | Open |
| 6 | Log aggregation | Consolidate worker logs into single view with filtering | Medium | Open |
| 7 | Task retry logic | Auto-retry failed tasks with backoff, max attempts | Medium | Open |
| 8 | Dry-run improvements | Better simulation of rush without actual execution | Medium | Open |
