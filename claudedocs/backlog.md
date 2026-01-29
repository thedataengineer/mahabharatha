# ZERG Development Backlog

**Updated**: 2026-01-28

## Completed

| # | Item | Completed | Commit |
|---|------|-----------|--------|
| 1 | State file IPC: Workers write WorkerState, orchestrator reloads in poll loop | 2026-01-28 | a189fc7 |
| 2 | Container execution: Docker image, ContainerLauncher, resource limits, health checks, security hardening | 2026-01-28 | ce7d58e |
| 4 | Debug cleanup: Gate verbose diagnostic details behind `--verbose` in troubleshoot.py | 2026-01-28 | 763ef8c |
| 3 | Test coverage: 96.53% coverage across 64 modules (4468 tests), P0 files all at 100% | 2026-01-28 | 06abc7c + 1dc4f8e |

## Backlog

| # | Area | Description | Effort | Status |
|---|------|-------------|--------|--------|
| 5 | Production dogfooding | Never tested against a real feature build end-to-end | Large | Open |
| 6 | Log aggregation | Consolidate worker logs into single view with filtering | Medium | Open |
| 7 | Task retry logic | Auto-retry failed tasks with backoff, max attempts | Medium | Open |
| 8 | Dry-run improvements | Better simulation of rush without actual execution | Medium | Open |
