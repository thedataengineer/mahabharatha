# Architecture

> Understanding how MAHABHARATHA builds software in parallel - a guided journey through the system.

---

## The Journey of a Feature

When you type `/mahabharatha:kurukshetra`, something remarkable happens behind the scenes. Your vague idea transforms into coordinated action as multiple AI workers spring to life, each tackling a piece of your feature simultaneously. But how does MAHABHARATHA turn "I want user authentication" into working code across five parallel workers without chaos?

This guide tells that story. We'll follow a feature from inception to completion, meeting each component along the way and understanding why it exists.

### The Factory Floor

Think of MAHABHARATHA like a modern factory floor. You (the user) arrive with a product idea. The factory doesn't immediately start stamping metal - first, engineers translate your idea into blueprints. Then production planners break the blueprints into work orders that different stations can execute simultaneously. Workers at individual stations build components. Quality control inspects each stage. Finally, everything comes together into a finished product.

MAHABHARATHA works the same way:

| Factory Analogy | MAHABHARATHA Component | Purpose |
|----------------|----------------|---------|
| **Product Idea** | User requirements | What you want to build |
| **Engineering** | `/mahabharatha:plan` | Translate idea into specifications |
| **Blueprints** | `requirements.md` | The feature specification |
| **Production Planning** | `/mahabharatha:design` | Break work into parallel tasks |
| **Work Orders** | `task-graph.json` | Atomic units of work |
| **Factory Manager** | Orchestrator | Coordinates everything |
| **Assembly Workers** | Warriors | Claude Code instances writing code |
| **Workstations** | Git worktrees | Isolated work environments |
| **Quality Control** | Quality gates | Lint, typecheck, test |
| **Final Assembly** | Merge | Combine all work |

Now let's walk through each stage of this journey.

---

## Layer 1: Planning - Capturing the Vision

### What Is Planning?

Planning is the conversation phase where MAHABHARATHA helps you articulate what you want to build. Rather than accepting vague requirements and guessing wrong, MAHABHARATHA asks probing questions until both you and the system have a shared understanding.

### Why Does Planning Exist?

The most expensive bugs are requirements bugs - building the wrong thing entirely. Imagine our factory spending weeks manufacturing the wrong product because the initial order was unclear. By investing time upfront in clarifying what you want, MAHABHARATHA avoids the frustration of workers building features you didn't actually need.

### How the Story Flows

When you run `/mahabharatha:plan user-auth`, MAHABHARATHA doesn't immediately start coding. Instead, it engages in Socratic discovery:

```
You: "I want user authentication"

MAHABHARATHA: "Let me understand better:
  - What authentication methods? (password, OAuth, magic link?)
  - Should users be able to reset passwords?
  - Do you need role-based access control?
  - What's your security posture? (2FA, session management?)
```

Through this conversation, vague intentions crystallize into concrete requirements. The output is `requirements.md` - a document that workers will read as their mission brief.

```
User Requirements -> [Socratic Discovery] -> requirements.md
                                               |
                                               v
                                   .gsd/specs/{feature}/requirements.md
```

---

## Layer 2: Design - Breaking Down the Work

### What Is Design?

Design is where MAHABHARATHA transforms "what to build" into "how to build it." The design phase analyzes your requirements, proposes an architecture, and breaks the work into atomic tasks that can be executed in parallel without stepping on each other.

### Why Does Design Exist?

Parallel execution requires careful coordination. If two workers both try to modify the same file, you get merge conflicts. If a worker starts building a feature that depends on code that doesn't exist yet, it fails.

Design solves both problems through two key innovations:

**Exclusive File Ownership**: Each task declares which files it will create or modify. The design phase ensures no two tasks at the same level touch the same files. This eliminates merge conflicts without runtime locking.

**Level-Based Dependencies**: Tasks are organized into dependency levels. All workers must complete Level 1 (foundation types and schemas) before anyone starts Level 2 (business logic that uses those types). This ensures dependencies exist before they're needed.

### How the Story Flows

Running `/mahabharatha:design` produces two artifacts:

```
requirements.md -> [Architecture Analysis] -> task-graph.json + design.md
                                               |
                   +---------------------------+---------------------------+
                   v                           v                           v
           Level 1 Tasks              Level 2 Tasks              Level N Tasks
```

The `task-graph.json` looks like this:

```json
{
  "id": "TASK-001",
  "title": "Create User model",
  "level": 1,
  "files": {
    "create": ["src/models/user.py"],
    "modify": [],
    "read": ["src/config.py"]
  },
  "verification": {
    "command": "python -c \"from src.models.user import User\"",
    "timeout_seconds": 60
  }
}
```

Notice how the task declares exactly which files it owns. TASK-001 creates `user.py`. No other Level 1 task will touch that file.

### The Level System

Tasks flow through dependency levels like an assembly line:

| Level | Name | Description |
|-------|------|-------------|
| 1 | Foundation | Types, schemas, configuration |
| 2 | Core | Business logic, services |
| 3 | Integration | Wiring, endpoints |
| 4 | Testing | Unit and integration tests |
| 5 | Quality | Documentation, cleanup |

**The rule is simple**: All workers complete Level N before any proceed to Level N+1. The orchestrator merges all branches, runs quality gates, then signals workers to continue.

---

## Layer 3: Orchestration - The Factory in Motion

### What Is Orchestration?

Orchestration is the execution phase - when workers actually write code. The orchestrator spawns multiple Claude Code instances (warriors), each in its own isolated workspace, and coordinates their work through level-based execution.

### Why Does Orchestration Exist This Way?

Traditional development is sequential: one developer finishes, then another starts. MAHABHARATHA flips this by running workers in parallel wherever possible. But parallelism needs coordination.

Think of the orchestrator as the factory manager. The manager doesn't build anything directly - they:
- Assign work orders to workers
- Track who's doing what
- Know when a level is complete
- Trigger quality checks between levels
- Handle workers who crash or get stuck

### How the Story Flows

When you run `/mahabharatha:kurukshetra`, here's what happens:

```
[Orchestrator Start]
        |
        v
[Load task-graph.json] -> [Assign tasks to warriors]
        |
        v
[Create git worktrees] - Each worker gets their own copy of the codebase
        |
        v
[Spawn N warrior processes]
        |
        v
+---------------------------------------------------------------------+
|  FOR EACH LEVEL:                                                    |
|    1. Warriors execute tasks in PARALLEL                           |
|    2. Orchestrator polls until all level tasks complete             |
|    3. MERGE PROTOCOL:                                               |
|       - Merge all warrior branches -> staging branch               |
|       - Run quality gates (lint, typecheck, test)                   |
|       - Promote staging -> feature branch                           |
|    4. Rebase warrior branches onto merged state                    |
|    5. Advance to next level                                         |
+---------------------------------------------------------------------+
        |
        v
[All tasks complete] -> Feature branch ready for PR
```

### The Architecture Diagram

Here's how all the layers connect visually:

```
+---------------------------------------------------------------------+
|                        Layer 1: Planning                             |
|                 requirements.md + INFRASTRUCTURE.md                  |
|                    (/mahabharatha:plan, /mahabharatha:brainstorm)                   |
+---------------------------------------------------------------------+
                                |
                                v
+---------------------------------------------------------------------+
|                        Layer 2: Design                               |
|                  design.md + task-graph.json                        |
|                         (/mahabharatha:design)                              |
+---------------------------------------------------------------------+
                                |
                                v
+---------------------------------------------------------------------+
|                     Layer 3: Orchestration                           |
|    Warrior lifecycle - Level sync - Branch merging - Monitoring    |
|                          (/mahabharatha:kurukshetra)                               |
+---------------------------------------------------------------------+
          |                     |                     |
          v                     v                     v
+-------------+       +-------------+       +-------------+
| Warrior 0  |       | Warrior 1  |       | Warrior N  |
|  (worktree) |       |  (worktree) |       |  (worktree) |
+-------------+       +-------------+       +-------------+
          |                     |                     |
          +---------------------+---------------------+
                                |
                                v
+---------------------------------------------------------------------+
|                     Layer 4: Quality Gates                           |
|             Lint - Type-check - Test - Merge to main                |
|                        (/mahabharatha:merge)                                |
+---------------------------------------------------------------------+
```

---

## Warriors: The Individual Workers

### What Is a Warrior?

A warrior is a single Claude Code worker instance - an AI that reads the spec files and writes code to complete its assigned tasks. The name comes from the idea of overwhelming a feature with many small, focused workers rather than one monolithic process.

### Why Independent Execution?

If warriors shared state, a crash in one could corrupt data for all others. Shared conversation history would mean workers waiting for context windows to sync. Shared file systems would mean merge conflicts constantly.

By keeping warriors fully isolated, MAHABHARATHA achieves:
- **Crash recovery**: Just restart the failed worker
- **Horizontal scaling**: Add more workers without coordination overhead
- **Deterministic behavior**: Same inputs always produce same outputs

### The Isolation Layers

Each warrior operates in complete isolation through three layers:

```
+---------------------------------------------------------------------+
|                    WARRIOR ISOLATION LAYERS                         |
+---------------------------------------------------------------------+
| 1. Git Worktree: .mahabharatha-worktrees/{feature}-worker-{id}/             |
|    - Independent file system                                        |
|    - Separate git history                                           |
|    - Own branch: mahabharatha/{feature}/worker-{id}                         |
+---------------------------------------------------------------------+
| 2. Process Isolation                                                |
|    - Separate process per warrior                                  |
|    - Independent memory space                                       |
|    - Communication via state files only                             |
+---------------------------------------------------------------------+
| 3. Spec-Driven Execution                                            |
|    - No conversation history sharing                                |
|    - Read specs fresh each time                                     |
|    - Stateless, restartable                                         |
+---------------------------------------------------------------------+
```

**Layer 1 (Git Worktree)** gives each worker its own copy of the codebase. Git worktrees are a built-in feature that creates independent working directories sharing the same repository. Worker 0 can edit files in its worktree while Worker 1 edits different files in its worktree - no conflicts possible.

**Layer 2 (Process Isolation)** means each worker runs as a separate OS process. If Worker 2 crashes, Workers 0, 1, and 3 keep running. Communication happens through files on disk (the state JSON), not shared memory.

**Layer 3 (Spec-Driven Execution)** is the key to restartability. Workers don't remember previous conversations - they read the spec files fresh every time. If a worker crashes mid-task, just restart it. It will read the specs, see the task is incomplete, and pick up where it left off.

### The Worker Protocol

Each warrior follows a strict protocol:

1. **Claim**: Mark task `in_progress` via TaskUpdate
2. **Load**: Read `requirements.md`, `design.md`, task context
3. **Execute**: Implement according to task specification
4. **Verify**: Run verification command from task-graph.json
5. **Commit**: Stage owned files, commit with task ID
6. **Report**: Mark task `completed` or `failed` via TaskUpdate

---

## Layer 4: Quality Gates - Protecting the Codebase

### What Are Quality Gates?

Quality gates are automated checks that run between levels. They ensure nothing broken reaches your main branch. After each level completes, gates run linting, type checking, and tests. Only code that passes all gates gets merged.

### Why Do Quality Gates Exist?

Parallel development means multiple workers making changes simultaneously. Without quality gates, broken code could slip through and cascade into later levels. Quality gates act like the factory's quality control department - inspecting each batch before it moves to the next station.

### How Quality Gates Flow

```yaml
# .mahabharatha/config.yaml
quality_gates:
  lint:
    command: "ruff check ."
    required: true
  typecheck:
    command: "mypy ."
    required: false
  test:
    command: "pytest"
    required: true
```

| Result | What It Means | What Happens |
|--------|---------------|--------------|
| `pass` | Exit code 0 | Continue to merge |
| `fail` | Non-zero exit | Block if required gate |
| `timeout` | Exceeded limit | Treat as failure |
| `error` | Could not run | Pause for intervention |

### Per-Task Verification

Beyond level gates, each task includes its own verification command:

```json
{
  "id": "TASK-001",
  "verification": {
    "command": "python -c \"from src.models.user import User\"",
    "timeout_seconds": 60
  }
}
```

This ensures the task actually works before being marked complete. Pass or fail, no subjectivity.

---

## Data Flow: The Complete Journey

Now let's trace how data flows from your initial idea to finished code. Understanding this flow helps you know what's happening at any point and where to look when something goes wrong.

### The Spec-to-Execution Pipeline

```
User Requirements
       |
       v
/mahabharatha:plan --> requirements.md
       |            |
       v            v
/mahabharatha:design --> design.md + task-graph.json
       |                          |
       v                          v
/mahabharatha:kurukshetra --> Worker Assignments + State
       |              |
       +------+-------+
              |
              v
       [Worker 0]    [Worker 1]    [Worker N]
              |              |              |
              v              v              v
       [Task Execution in Isolated Worktrees]
              |              |              |
              +------+-------+------+-------+
                     |
                     v
              [Level Complete]
                     |
                     v
              [Merge Protocol]
                     |
                     v
              [Quality Gates]
                     |
                     v
              [Next Level or Done]
```

### File Locations

Where does everything live? Here's your map:

| Artifact | Path | Purpose |
|----------|------|---------|
| Requirements | `.gsd/specs/{feature}/requirements.md` | What to build |
| Design | `.gsd/specs/{feature}/design.md` | How to build it |
| Task Graph | `.gsd/specs/{feature}/task-graph.json` | Atomic work units |
| State | `.mahabharatha/state/{feature}.json` | Runtime state |
| Worker Logs | `.mahabharatha/logs/workers/worker-{id}.jsonl` | Structured events |
| Task Artifacts | `.mahabharatha/logs/tasks/{task-id}/` | Per-task outputs |
| Worktrees | `.mahabharatha-worktrees/{feature}-worker-{N}/` | Isolated filesystems |

### State Management

Workers coordinate through two systems:

**Claude Code Tasks** (authoritative): The Task system is the source of truth for task state. Workers claim tasks by calling TaskUpdate, and `/mahabharatha:status` reads state via TaskList.

**State JSON** (supplementary): Fast local file with worker-level details like context usage and branch names. If Tasks and state JSON disagree, **Tasks win**.

```
/mahabharatha:design -> TaskCreate for each task --> Subject: "[L{level}] {title}"
    |
    v
/mahabharatha:kurukshetra
    |
    v
TaskUpdate (in_progress) --> Worker claims task
    |
    v
Worker executes
    |
    v
TaskUpdate (completed/failed) --> Worker reports result
    |
    v
/mahabharatha:status
    |
    v
TaskList --> Read current state across all workers
```

---

## Key Concepts Summary

### Spec as Memory

Warriors do not share conversation context. They share specifications:
- `requirements.md` - what to build
- `design.md` - how to build it
- `task-graph.json` - atomic work units

This makes warriors **stateless**. Any warrior can pick up any task. Crash recovery is trivial.

### File Ownership

Each task declares exclusive file ownership. No overlap within a level:

```json
{
  "id": "TASK-001",
  "files": {
    "create": ["src/models/user.py"],
    "modify": ["src/config.py"],
    "read": ["src/types.py"]
  }
}
```

Benefits:
- No merge conflicts within levels
- No runtime locking needed
- Any worker can pick up any task

### Worktree Isolation

Each worker operates in its own git worktree:

```
.mahabharatha-worktrees/{feature}/worker-0/  ->  branch: mahabharatha/{feature}/worker-0
.mahabharatha-worktrees/{feature}/worker-1/  ->  branch: mahabharatha/{feature}/worker-1
```

Workers commit independently. No filesystem conflicts.

---

## Module Reference

MAHABHARATHA comprises 80+ Python modules organized into functional groups. Here's how they connect to the journey we've traced.

### Core Orchestration

These modules implement the factory manager role:

| Module | Path | Responsibility |
|--------|------|----------------|
| `orchestrator` | `mahabharatha/orchestrator.py` | Fleet management, level transitions, merge triggers |
| `levels` | `mahabharatha/levels.py` | Level-based execution control, dependency enforcement |
| `state` | `mahabharatha/state.py` | Thread-safe file-based state persistence |
| `worker_protocol` | `mahabharatha/worker_protocol.py` | Warrior-side execution, Claude Code invocation |
| `launcher` | `mahabharatha/launcher.py` | Abstract worker spawning (subprocess/container/task) |

### Task Management

These modules handle work order processing:

| Module | Path | Responsibility |
|--------|------|----------------|
| `assign` | `mahabharatha/assign.py` | Task-to-warrior assignment with load balancing |
| `parser` | `mahabharatha/parser.py` | Parse and validate task graphs |
| `verify` | `mahabharatha/verify.py` | Execute task verification commands |
| `task_sync` | `mahabharatha/task_sync.py` | Bridge between JSON state and Claude Tasks |

### Git Operations

These modules manage the worktree infrastructure:

| Module | Path | Responsibility |
|--------|------|----------------|
| `git_ops` | `mahabharatha/git_ops.py` | Low-level git operations |
| `worktree` | `mahabharatha/worktree.py` | Git worktree management for warrior isolation |
| `merge` | `mahabharatha/merge.py` | Branch merging after each level |

### Quality & Security

These modules implement the quality control department:

| Module | Path | Responsibility |
|--------|------|----------------|
| `gates` | `mahabharatha/gates.py` | Execute quality gates (lint, typecheck, test) |
| `security` | `mahabharatha/security.py` | Security validation, hook patterns |
| `validation` | `mahabharatha/validation.py` | Task graph and ID validation |

---

## Execution Modes

MAHABHARATHA supports three ways to run workers, like a factory that can use different types of machinery:

| Mode | How Workers Run | When To Use |
|------|-----------------|-------------|
| `task` | Claude Code Task sub-agents | Inside Claude Code (default) |
| `subprocess` | Local processes | Development, debugging |
| `container` | Docker containers | Reproducibility, CI |

The system auto-detects the best mode, but you can override with `--mode subprocess` or `--mode container`.

---

## Related Documentation

Now that you understand the architecture, explore deeper:

- [Commands](./Commands.md) - CLI command reference
- [Configuration](./Configuration.md) - Config file options
- [Troubleshooting](./Troubleshooting.md) - Common issues and fixes

---

*Generated from [ARCHITECTURE.md](/ARCHITECTURE.md)*
