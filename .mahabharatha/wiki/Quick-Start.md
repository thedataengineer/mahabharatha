# Quick Start

This page walks through the full MAHABHARATHA workflow from initialization to merged code. Each step shows the command, what it does, and what to expect.

**Time estimate:** 15 to 30 minutes for a small feature (3 to 5 tasks).

**Prerequisites:** MAHABHARATHA installed, Claude Code available, git repository initialized. See [[Installation]] if you have not set up yet.

---

## Table of Contents

- [Step 1: Initialize](#step-1-initialize)
- [Step 2: Plan](#step-2-plan)
- [Step 3: Design](#step-3-design)
- [Step 4: Kurukshetra](#step-4-kurukshetra)
- [Step 5: Monitor](#step-5-monitor)
- [Step 6: Merge](#step-6-merge)
- [What Happens Next](#what-happens-next)

---

## Step 1: Initialize

Open Claude Code in your project directory and run the init command.

```
/mahabharatha:init
```

**What it does:**

- Detects your project's languages and frameworks.
- Creates the `.mahabharatha/` directory with `config.yaml`.
- Generates `.devcontainer/` configuration (for container mode).
- Creates `.gsd/` directory for specs and project metadata.

**Expected output:**

```
MAHABHARATHA Init - Discovery Mode
Detected languages: python
Detected frameworks: fastapi
Created .mahabharatha/config.yaml
Created .devcontainer/
Created .gsd/PROJECT.md
Initialization complete.
```

**Verification:** Confirm the directories exist.

```bash
ls -la .mahabharatha/config.yaml .gsd/PROJECT.md
```

You only need to run `/mahabharatha:init` once per project. Skip this step if your project is already initialized.

---

## Step 1.5: Brainstorm (Optional)

If you are not sure what to build yet, use the brainstorm command to explore ideas before planning.

```
/mahabharatha:brainstorm --socratic
```

**What it does:**

- Optionally researches the competitive landscape via web search.
- Conducts structured Socratic questioning rounds to refine ideas.
- For single-question mode: provide a focused question with structured answer options.
- Creates prioritized GitHub issues from the results.
- Suggests a top-priority feature to pass to `/mahabharatha:plan`.

**Enhanced Pipeline:**

The brainstorm output goes through validation (trade-offs vs. scope), followed by a YAGNI gate to prevent speculative scope creep. This ensures ideas are grounded in current requirements.

This step is entirely optional. If you already know what feature to build, skip directly to Step 2.

See [[mahabharatha-brainstorm]] for full details and options.

---

## Step 2: Plan

Tell MAHABHARATHA what feature to build.

```
/mahabharatha:plan user-auth
```

**What it does:**

- Creates a spec directory at `.gsd/specs/user-auth/`.
- Reads your existing codebase to understand the current state.
- Asks you clarifying questions about the feature.
- Generates `requirements.md` from your answers.
- Asks for your explicit approval.

**What to expect:**

MAHABHARATHA will ask questions in groups. Answer each group, then MAHABHARATHA will ask follow-up questions based on your answers. A typical planning session has 2 to 4 rounds of questions.

```
Planning: user-auth

Context gathered. I have some questions:

1. What authentication method do you need? (JWT, session, OAuth, etc.)
2. What user data needs to be stored?
3. Are there existing user tables or is this greenfield?
4. What endpoints do you need? (register, login, logout, refresh?)
```

After you answer all questions, MAHABHARATHA generates the requirements document and asks for approval.

**Approval:**

```
Requirements ready for review.
Reply with "APPROVED" to proceed, or describe changes needed.
```

Type `APPROVED` (case-insensitive) to proceed. If something is wrong, describe what needs to change and MAHABHARATHA will revise.

**Verification:** Confirm the requirements file exists and is marked approved.

```bash
head -20 .gsd/specs/user-auth/requirements.md
```

---

## Step 3: Design

Generate the technical architecture and task graph.

```
/mahabharatha:design
```

**What it does:**

- Reads the approved requirements.
- Designs the component architecture with data flows and interfaces.
- Breaks the work into atomic tasks with exclusive file ownership.
- Assigns tasks to dependency levels.
- Generates `design.md` and `task-graph.json`.
- Registers all tasks in Claude Code's Task system.
- Asks for your approval.

**Expected output (summary):**

```
DESIGN READY FOR REVIEW

Feature: user-auth

Architecture:
  - 4 components
  - 3 key decisions documented

Task Graph:
  - 9 total tasks across 5 levels
  - Max parallelization: 3 workers
  - Estimated duration: 3h (single) -> 1h (3 workers)

Reply with "approved" to proceed or "changes needed".
```

**What to review before approving:**

| Check | Why It Matters |
|-------|----------------|
| File ownership is exclusive | Prevents merge conflicts during parallel execution |
| Verification commands are meaningful | Weak verification leads to incomplete implementations |
| Level assignments make sense | Wrong levels cause unnecessary serialization |
| Task count is reasonable | Too many small tasks adds overhead; too few limits parallelism |

Type `approved` to proceed.

**Verification:** Confirm the task graph is valid JSON.

```bash
jq '.total_tasks, .max_parallelization' .gsd/specs/user-auth/task-graph.json
```

---

## Step 4: Kurukshetra

Launch parallel workers to execute the task graph.

```
/mahabharatha:kurukshetra --workers=3
```

**What it does:**

- Reads the task graph and worker assignments.
- Creates git worktrees for each worker (one branch per worker).
- Launches Claude Code instances (one per worker).
- Each worker claims its assigned tasks and begins execution.
- Workers execute Level 1 tasks first, then wait for merge before Level 2.

**Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--workers=N` | 5 | Number of parallel workers |
| `--mode container` | subprocess | Run workers in Docker containers |
| `--resume` | off | Resume from a previous interrupted kurukshetra |

**Expected output:**

```
Launching MAHABHARATHA Kurukshetra: user-auth

Task graph: 9 tasks across 5 levels
Workers: 3 (adjusted from 5 -- max parallelization is 3)

Launching Worker 0 on port 49152...
Launching Worker 1 on port 49153...
Launching Worker 2 on port 49154...

All workers launched. Orchestrator running (PID: 12345).

Monitor progress in a separate terminal:
  mahabharatha status --dashboard
```

**Important:** The `/mahabharatha:kurukshetra` command occupies the current Claude Code session. Open a separate terminal for monitoring (see Step 5).

---

## Step 5: Monitor

Check progress from a separate terminal.

### Option A: Live Dashboard (Recommended)

```bash
mahabharatha status --dashboard
```

This opens a TUI with live-updating progress bars, worker status, and event streaming.

### Option B: Text Refresh

```bash
mahabharatha status --watch --interval 2
```

### Option C: One-Shot Check

From a separate Claude Code session:

```
/mahabharatha:status
```

**Example status output:**

```
FACTORY STATUS

Feature:      user-auth
Phase:        EXECUTING
Orchestrator: Running (PID: 12345)
Elapsed:      00:12:34

PROGRESS

Overall: [=========>          ] 44% (4/9 tasks)

Level 1 (Foundation):   [====================] COMPLETE (2/2 tasks)
Level 2 (Core):         [==========>         ] IN PROGRESS (2/3 tasks)
Level 3 (Integration):  [                    ] PENDING (0/2 tasks)
Level 4 (Testing):      [                    ] PENDING (0/1 tasks)
Level 5 (Quality):      [                    ] PENDING (0/1 tasks)
```

---

## Step 6: Merge

Merging happens automatically after each level completes. The orchestrator:

1. Collects all worker branches for the completed level.
2. Merges them into a staging branch.
3. Runs quality gates (lint, typecheck, tests).
4. If gates pass, advances to the next level.
5. If gates fail, execution pauses until issues are resolved.

You can also trigger a merge manually:

```
/mahabharatha:merge
```

**Quality gates** are defined in `.mahabharatha/config.yaml`. The default gates are:

| Gate | Command | Required |
|------|---------|----------|
| lint | `ruff check .` | Yes |
| typecheck | `mypy . --strict --ignore-missing-imports` | Yes |
| test | `pytest tests/unit/ -x --timeout=30` | Yes |
| coverage | `pytest tests/unit/ --cov=mahabharatha --cov-fail-under=80` | No |
| security | `ruff check . --select S` | No |

**If a quality gate fails:**

- Execution pauses at the current level.
- The status dashboard shows which gate failed and the error output.
- You can fix the issue manually, or use `/mahabharatha:retry <task-id>` to re-run a specific task.
- After fixing, run `/mahabharatha:merge` to retry the merge and quality gates.

---

## What Happens Next

After all levels complete and quality gates pass, your feature code is on the `mahabharatha/<feature>/base` branch.

**To integrate into your main branch:**

```bash
git checkout main
git merge mahabharatha/user-auth/base
```

**To clean up MAHABHARATHA artifacts:**

```
/mahabharatha:cleanup
```

This removes worktrees, worker branches, and temporary state files.

---

## Common Issues During a Kurukshetra

| Symptom | Cause | Fix |
|---------|-------|-----|
| Worker exits immediately | Missing API key or auth | Check `ANTHROPIC_API_KEY` or OAuth setup |
| "Task graph not found" | Skipped the design step | Run `/mahabharatha:design` first |
| Quality gate fails on merge | Worker produced code with lint/type errors | Fix manually or `/mahabharatha:retry` the task |
| Workers idle at next level | Previous level merge not triggered | Run `/mahabharatha:merge` manually |
| "Port already in use" | Previous workers did not shut down | Run `/mahabharatha:stop` then retry |

---

## Next Steps

- [[Your First Feature]] -- Detailed walkthrough with a real example.
- [[Getting Started]] -- Deeper explanation of core concepts.
