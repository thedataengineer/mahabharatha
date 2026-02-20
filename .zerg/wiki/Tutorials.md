# Tutorials

Step-by-step guides for building features with MAHABHARATHA. Each tutorial walks through a complete workflow from planning to merge.

## Prerequisites

Before starting any tutorial, confirm the following:

- Claude Code is installed and authenticated
- Docker is installed and running (required for container mode tutorials)
- You have cloned the MAHABHARATHA repository and can run `mahabharatha --help`
- You understand the basic MAHABHARATHA lifecycle: **Brainstorm (optional) -> Plan -> Design -> Kurukshetra -> Merge**

## Available Tutorials

### [[Tutorial-Minerals-Store]]

**Difficulty**: Intermediate
**Estimated time**: 30-45 minutes
**Mode**: Subprocess (default)

A complete walkthrough building a hypothetical "minerals store" e-commerce feature. Covers every phase of the MAHABHARATHA workflow with realistic task-graph examples, file ownership matrices, and quality gate output. Start here if you are new to MAHABHARATHA.

Topics covered:

- Capturing requirements with `/mahabharatha:plan`
- Generating architecture and task graphs with `/mahabharatha:design`
- Launching parallel workers with `/mahabharatha:kurukshetra`
- Merging level results and running quality gates with `/mahabharatha:merge`
- Monitoring progress with `/mahabharatha:status`

### [[Tutorial-Container-Mode]]

**Difficulty**: Advanced
**Estimated time**: 45-60 minutes
**Mode**: Container (`--mode container`)

A guide to running MAHABHARATHA workers inside Docker containers for isolated, reproducible execution. Covers Docker image setup, authentication methods (OAuth and API key), resource limits, volume mounts, and debugging failed containers.

Topics covered:

- Building the `mahabharatha-worker` Docker image
- Configuring container resource limits (CPU, memory)
- OAuth authentication via `~/.claude` mount
- API key authentication via `ANTHROPIC_API_KEY`
- Git worktree mounts and state sharing
- Inspecting and debugging container workers
- Troubleshooting common container failures

## Concept Reference

If you need a refresher on MAHABHARATHA terminology before starting a tutorial:

| Concept | Description |
|---------|-------------|
| **Level** | A group of tasks with the same dependency depth. All tasks in Level 1 must complete before any Level 2 task starts. |
| **File Ownership** | Each task owns exclusive files. No two tasks at the same level write to the same file. This prevents merge conflicts. |
| **Task Graph** | A JSON file (`task-graph.json`) defining all tasks, their dependencies, file ownership, and verification commands. |
| **Quality Gates** | Automated checks (lint, typecheck, test) that run after merging each level. Failures block progression. |
| **Worktree** | A git worktree created per worker, giving each worker its own working directory on a separate branch. |
| **Orchestrator** | The process that coordinates workers, manages level transitions, and triggers merges. |

## Further Reading

- Project README: `CLAUDE.md` in the repository root
- Configuration reference: `.mahabharatha/config.yaml`
- Command reference: `mahabharatha/data/commands/mahabharatha:*.md`
