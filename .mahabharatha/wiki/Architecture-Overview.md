# Architecture Overview

MAHABHARATHA is a parallel Claude Code execution system that coordinates multiple worker instances to implement features concurrently. This page describes the high-level architecture, core abstractions, and design principles that govern the system.

## System Architecture

The system follows a layered architecture where the CLI accepts user commands, the orchestrator coordinates execution, launchers spawn workers, and workers execute tasks in isolated git worktrees.

```mermaid
graph TB
    subgraph "User Interface"
        CLI["CLI (click)"]
    end

    subgraph "Coordination Layer"
        ORCH["Orchestrator"]
        LC["LevelCoordinator"]
        WM["WorkerManager"]
        TRM["TaskRetryManager"]
        SSS["StateSyncService"]
    end

    subgraph "Infrastructure Layer"
        LAUNCH["Launcher (ABC)"]
        SUB["SubprocessLauncher"]
        CONT["ContainerLauncher"]
        GIT["GitOps"]
        WT["WorktreeManager"]
        PORTS["PortAllocator"]
    end

    subgraph "Execution Layer"
        W1["Worker 0"]
        W2["Worker 1"]
        W3["Worker N"]
    end

    subgraph "State Layer"
        STATE["StateManager"]
        TASKS["Claude Code Tasks"]
        TSYNC["TaskSync"]
        JSON[".mahabharatha/state/*.json"]
    end

    CLI --> ORCH
    ORCH --> LC
    ORCH --> WM
    ORCH --> TRM
    ORCH --> SSS
    LC --> LAUNCH
    WM --> LAUNCH
    LAUNCH --> SUB
    LAUNCH --> CONT
    WM --> WT
    WM --> PORTS
    SUB --> W1
    SUB --> W2
    CONT --> W3
    W1 --> STATE
    W2 --> STATE
    W3 --> STATE
    SSS --> STATE
    TSYNC --> STATE
    TSYNC --> TASKS
    STATE --> JSON
    ORCH --> GIT
    LC --> GIT
```

## Core Concepts

### Task Graph

Every feature begins with a **task graph** (`task-graph.json`) produced by the `design` phase. The task graph defines:

- **Tasks**: Atomic units of work, each with a unique ID, title, description, file ownership, dependencies, and a verification command.
- **Levels**: Tasks are grouped into dependency levels. Level 1 tasks have no dependencies. Level 2 tasks depend only on Level 1 tasks, and so on.
- **File Ownership**: Each task declares the files it creates and modifies. No two tasks at the same level may own the same file, which eliminates merge conflicts within a level.

### Level-Based Execution

MAHABHARATHA enforces a strict execution order by level:

1. All workers execute their assigned Level 1 tasks in parallel.
2. When every Level 1 task completes, the orchestrator merges all worker branches into a staging branch and runs quality gates.
3. Workers pull the merged result and begin Level 2 tasks.
4. This repeats until all levels are complete.

```mermaid
graph LR
    L1["Level 1: Foundation"] --> M1["Merge + Gates"]
    M1 --> L2["Level 2: Core"]
    L2 --> M2["Merge + Gates"]
    M2 --> L3["Level 3: Integration"]
    L3 --> M3["Merge + Gates"]
    M3 --> DONE["Complete"]
```

This guarantees that downstream tasks always see a consistent, merged codebase from prior levels.

### File Ownership

File ownership is the mechanism that prevents merge conflicts. The design phase assigns each file to exactly one task per level. Workers operating on different files can proceed in parallel without coordination beyond level boundaries.

| Concept | Scope | Purpose |
|---------|-------|---------|
| Task | Single unit of work | Owns specific files, has verification command |
| Level | Group of independent tasks | All tasks at a level run concurrently |
| Worker | Claude Code instance | Executes assigned tasks in an isolated worktree |
| Worktree | Git worktree per worker | Provides filesystem isolation |

### Worker Isolation

Each worker runs in its own git worktree on a dedicated branch. Workers do not share a working directory. Communication between workers happens exclusively through:

- The shared **state JSON** file (with file-level locking via `fcntl.flock`).
- The **Claude Code Task system** (the authoritative source of truth for task status).

### Launcher Backends

Workers can be spawned via two backends:

- **SubprocessLauncher**: Runs Claude Code as a local subprocess. Suitable for development and single-machine execution.
- **ContainerLauncher**: Runs Claude Code inside Docker containers with bind-mounted worktrees. Required for production isolation and multi-user scenarios.

Both backends implement the `WorkerLauncher` abstract base class defined in `launcher.py`.

## Configuration

System behavior is controlled by `.mahabharatha/config.yaml`, which configures:

- Worker count and timeout limits
- Launcher type (subprocess or container)
- Quality gate commands
- Port allocation ranges
- Plugin and context engineering settings
- Retry and backpressure thresholds

See [[Architecture-State-Management]] for details on configuration and state files.

## Related Pages

- [[Architecture-Execution-Flow]] -- Step-by-step walkthrough of the plan-to-merge lifecycle.
- [[Architecture-Module-Reference]] -- Complete reference of all Python modules.
- [[Architecture-State-Management]] -- State files, Claude Tasks integration, and persistence.
- [[Architecture-Dependency-Graph]] -- Module import relationships visualized.
