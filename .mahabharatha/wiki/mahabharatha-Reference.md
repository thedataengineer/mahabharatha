# MAHABHARATHA Command Reference

This page provides an index of all 26 MAHABHARATHA commands. Each command has its own detailed reference page.

## Workflow Overview

MAHABHARATHA commands follow a sequential workflow. The typical order of operations is:

```
brainstorm (optional) --> init --> plan --> design --> kurukshetra --> status/logs --> merge --> cleanup
```

During execution, use `stop` to halt workers, `retry` to re-run failed tasks, and `logs` to inspect worker output.

## Global CLI Flags

These flags apply to all MAHABHARATHA commands:

| Flag | Description |
|------|-------------|
| `--quick` | Surface-level analysis |
| `--think` | Structured multi-step analysis |
| `--think-hard` | Deep architectural analysis |
| `--ultrathink` | Maximum depth, all MCP servers |
| `--no-compact` | Disable compact output (compact is ON by default) |
| `--no-loop` | Disable improvement loops (loops are ON by default) |
| `--iterations N` | Override loop iteration count |
| `--mode MODE` | Behavioral mode: precision, speed, exploration, refactor, debug |
| `--mcp` / `--no-mcp` | Enable/disable MCP auto-routing |
| `--tdd` | Enable TDD enforcement |
| `-v` / `--verbose` | Verbose output |
| `-q` / `--quiet` | Suppress non-essential output |

## Command Index

| Command | Purpose | Phase |
|---------|---------|-------|
| [[/mahabharatha:init|mahabharatha-init]] | Initialize MAHABHARATHA for a new or existing project | Setup |
| [[/mahabharatha:brainstorm|mahabharatha-brainstorm]] | Feature discovery with Socratic dialogue, `--socratic` mode, trade-off exploration, and YAGNI filtering | Planning |
| [[/mahabharatha:plan|mahabharatha-plan]] | Capture requirements for a feature | Planning |
| [[/mahabharatha:design|mahabharatha-design]] | Generate architecture and task graph for parallel execution | Design |
| [[/mahabharatha:kurukshetra|mahabharatha-kurukshetra]] | Launch parallel workers to execute the task graph | Execution |
| [[/mahabharatha:status|mahabharatha-status]] | Display current execution status and progress | Monitoring |
| [[/mahabharatha:logs|mahabharatha-logs]] | Stream, filter, and aggregate worker logs | Monitoring |
| [[/mahabharatha:stop|mahabharatha-stop]] | Stop workers gracefully or forcefully | Control |
| [[/mahabharatha:retry|mahabharatha-retry]] | Retry failed or blocked tasks | Recovery |
| [[/mahabharatha:merge|mahabharatha-merge]] | Trigger or manage level merge operations | Integration |
| [[/mahabharatha:cleanup|mahabharatha-cleanup]] | Remove MAHABHARATHA artifacts and clean up resources | Teardown |
| [[/mahabharatha:build|mahabharatha-build]] | Build orchestration with error recovery | Quality |
| [[/mahabharatha:test|mahabharatha-test]] | Execute tests with coverage and generation | Quality |
| [[/mahabharatha:analyze|mahabharatha-analyze]] | Static analysis, complexity metrics, quality assessment | Quality |
| [[/mahabharatha:review|mahabharatha-review]] | Two-stage code review (spec compliance + quality) | Quality |
| [[/mahabharatha:security|mahabharatha-security]] | Vulnerability scanning and secure coding rules | Quality |
| [[/mahabharatha:refactor|mahabharatha-refactor]] | Automated code improvement and cleanup | Quality |
| [[/mahabharatha:git|mahabharatha-git]] | Git operations: commits, PRs, releases, rescue, review, bisect, ship, cleanup, issue (14 actions) | Utility |
| [[/mahabharatha:debug|mahabharatha-debug]] | Deep diagnostic investigation with Bayesian hypothesis testing | Utility |
| [[/mahabharatha:worker|mahabharatha-worker]] | Internal: warrior execution protocol | Utility |
| [[/mahabharatha:plugins|mahabharatha-plugins]] | Plugin system management | Utility |
| [[/mahabharatha:document|mahabharatha-document]] | Generate documentation for a specific component | Documentation |
| [[/mahabharatha:index|mahabharatha-index]] | Generate a complete project documentation wiki | Documentation |
| [[/mahabharatha:estimate|mahabharatha-estimate]] | Effort estimation with PERT intervals and cost projection | AI & Analysis |
| [[/mahabharatha:explain|mahabharatha-explain]] | Educational code explanations with progressive depth | AI & Analysis |
| [[/mahabharatha:select-tool|mahabharatha-select-tool]] | Intelligent tool routing for MCP servers and agents | AI & Analysis |

## Command Categories

### Setup

- **[[/mahabharatha:init|mahabharatha-init]]** -- Run once per project to detect languages, generate configuration, and create the `.mahabharatha/` directory structure.

### Planning and Design

- **[[/mahabharatha:brainstorm|mahabharatha-brainstorm]]** -- Open-ended feature discovery through competitive research, Socratic questioning with `--socratic` mode, trade-off exploration, YAGNI filtering, and automated issue creation.
- **[[/mahabharatha:plan|mahabharatha-plan]]** -- Interactive requirements gathering. Produces `requirements.md` in the spec directory.
- **[[/mahabharatha:design|mahabharatha-design]]** -- Generates `design.md` and `task-graph.json`. Breaks work into parallelizable tasks with exclusive file ownership.

### Execution

- **[[/mahabharatha:kurukshetra|mahabharatha-kurukshetra]]** -- Launches worker containers or processes. Assigns tasks by level and monitors execution.
- **[[/mahabharatha:stop|mahabharatha-stop]]** -- Graceful or forced shutdown of running workers.
- **[[/mahabharatha:retry|mahabharatha-retry]]** -- Re-queues failed tasks for execution.

### Monitoring

- **[[/mahabharatha:status|mahabharatha-status]]** -- Snapshot of progress across all levels, workers, and tasks.
- **[[/mahabharatha:logs|mahabharatha-logs]]** -- Access structured JSONL logs, filter by worker, task, level, phase, or event type.

### Integration and Teardown

- **[[/mahabharatha:merge|mahabharatha-merge]]** -- Merges worker branches after each level, runs quality gates (lint, test, typecheck).
- **[[/mahabharatha:cleanup|mahabharatha-cleanup]]** -- Removes worktrees, branches, containers, and state files. Preserves spec files and merged code.

### Quality and Analysis

- **[[/mahabharatha:build|mahabharatha-build]]** -- Build orchestration with automatic error recovery and watch mode.
- **[[/mahabharatha:test|mahabharatha-test]]** -- Test execution with coverage reporting, parallel runs, and test generation.
- **[[/mahabharatha:analyze|mahabharatha-analyze]]** -- Static analysis including linting, complexity metrics, coverage, and security checks.
- **[[/mahabharatha:review|mahabharatha-review]]** -- Two-stage code review: spec compliance verification followed by quality assessment.
- **[[/mahabharatha:security|mahabharatha-security]]** -- Vulnerability scanning with OWASP, PCI, HIPAA, and SOC2 presets.
- **[[/mahabharatha:refactor|mahabharatha-refactor]]** -- Automated code improvement: dead code removal, simplification, type additions, naming fixes.

### Utilities

- **[[/mahabharatha:git|mahabharatha-git]]** -- Git operations: commit, branch, merge, sync, history, finish, pr, release, review, rescue, bisect, ship, cleanup, issue (14 actions).
- **[[/mahabharatha:debug|mahabharatha-debug]]** -- Deep diagnostic investigation with Bayesian hypothesis testing and recovery plans.
- **[[/mahabharatha:worker|mahabharatha-worker]]** -- Internal warrior execution protocol. Not invoked directly by users.
- **[[/mahabharatha:plugins|mahabharatha-plugins]]** -- Plugin system management: quality gates, lifecycle hooks, and custom launchers.

### Documentation and AI

- **[[/mahabharatha:document|mahabharatha-document]]** -- Generate documentation for a specific component, module, or command using the doc_engine pipeline.
- **[[/mahabharatha:index|mahabharatha-index]]** -- Generate a complete project documentation wiki with cross-references and sidebar.
- **[[/mahabharatha:estimate|mahabharatha-estimate]]** -- Full-lifecycle effort estimation with PERT intervals, post-execution comparison, and calibration.
- **[[/mahabharatha:explain|mahabharatha-explain]]** -- Educational code explanations with four progressive depth layers.
- **[[/mahabharatha:select-tool|mahabharatha-select-tool]]** -- Intelligent tool routing across MCP servers, native tools, and Task agent subtypes.

## Global Concepts

### Feature Name

Most commands auto-detect the active feature from `.gsd/.current-feature`. You can override this with `--feature <name>` where supported.

### Task System

All commands integrate with Claude Code's Task system for coordination and state tracking. The Task system is the authoritative source of truth; state JSON files in `.mahabharatha/state/` are supplementary.

### Levels

Tasks are grouped into dependency levels. All tasks in Level N must complete before any Level N+1 task begins. Within a level, tasks run in parallel.

### File Ownership

Each task exclusively owns specific files. No two tasks modify the same file, which eliminates merge conflicts during parallel execution.
