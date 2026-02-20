# Debug Guide

This guide covers how to diagnose and resolve issues in MAHABHARATHA using built-in tooling, log analysis, and state inspection.

For quick answers to common problems, see [[Troubleshooting]].

---

## Table of Contents

- [Using /mahabharatha:debug](#using-zergdebug)
- [Reading Logs](#reading-logs)
- [Inspecting Task State](#inspecting-task-state)
- [Common Error Patterns](#common-error-patterns)
- [Advanced Diagnostics](#advanced-diagnostics)

---

## Using /mahabharatha:debug

The `/mahabharatha:debug` command is the primary diagnostic tool. It runs a multi-phase investigation: context gathering, error intelligence, symptom classification, hypothesis testing, and recovery planning.

### Basic Usage

```
/mahabharatha:debug
```

When run without arguments, it auto-detects the active feature from `.gsd/.current-feature` and performs a standard diagnostic pass.

### Targeting a Specific Problem

Pass a plain-text description of the problem:

```
/mahabharatha:debug workers keep crashing after level 2
```

Or target a specific worker:

```
/mahabharatha:debug --worker w3 --feature my-feature
```

### Flags Reference

| Flag | Short | Purpose |
|------|-------|---------|
| `--feature <name>` | `-f` | Investigate a specific feature |
| `--worker <id>` | `-w` | Focus on a single worker |
| `--deep` | | Run system-level checks (git, disk, Docker, ports, worktrees) |
| `--env` | | Environment diagnostics (Python, Docker, resources, config) |
| `--fix` | | Generate and execute a recovery plan (prompts for confirmation) |
| `--error <msg>` | `-e` | Analyze a specific error message |
| `--stacktrace <path>` | `-s` | Analyze a stack trace file |
| `--report <path>` | | Write diagnostic report to a specific file |

### Diagnostic Phases

The debug command executes these phases in order:

1. **Context Gathering** -- Reads MAHABHARATHA state, logs, task graph, design doc, and git state in parallel. Produces a context snapshot.

2. **Error Intelligence** -- Parses errors from multiple languages (Python, JavaScript, Go, Rust, Java, C++). Fingerprints and deduplicates errors across workers. Traces "caused by" chains to find root errors.

3. **Symptom Classification** -- Assigns the problem to exactly one category:

   | Category | Typical Indicators |
   |----------|--------------------|
   | `WORKER_FAILURE` | Worker crashed, stopped unexpectedly, timeout |
   | `TASK_FAILURE` | Verification failed, code error in task output |
   | `STATE_CORRUPTION` | JSON parse error, orphaned tasks, inconsistent state |
   | `INFRASTRUCTURE` | Docker down, disk full, port conflict, worktree issue |
   | `CODE_ERROR` | Import error, syntax error, runtime exception |
   | `DEPENDENCY` | Missing package, version conflict |
   | `MERGE_CONFLICT` | Git merge failure during level advancement |
   | `UNKNOWN` | Does not fit other categories |

4. **Log Correlation** -- Reconstructs a timeline across workers, clusters events temporally, and tracks error evolution.

5. **Evidence Collection** -- Gathers category-specific evidence (files, logs, state, git history).

6. **Hypothesis Testing** -- Forms up to 3 hypotheses with Bayesian probability scoring and automated test commands.

7. **Root Cause Determination** -- Synthesizes findings into a root cause statement with a confidence level.

8. **Recovery Plan** -- Suggests fixes tagged by risk level:
   - `[SAFE]` -- Read-only or easily reversible actions
   - `[MODERATE]` -- File modifications with backup
   - `[DESTRUCTIVE]` -- State resets or force operations

9. **Design Escalation Check** -- If the issue is architectural, recommends running `/mahabharatha:design`.

### Output

The debug report is saved to `claudedocs/debug-<timestamp>.md` by default, or to the path specified by `--report`.

---

## Reading Logs

### Log Locations

| Log | Location | Contents |
|-----|----------|----------|
| Worker stderr | `.mahabharatha/logs/worker-<id>.stderr.log` | Worker errors, crashes, stack traces |
| Worker stdout | `.mahabharatha/logs/worker-<id>.stdout.log` | Worker progress, task output |
| Merge logs | `.mahabharatha/logs/merge-*.log` | Quality gate results, merge outcomes |
| Debug reports | `claudedocs/debug-<timestamp>.md` | Full diagnostic reports |

### Tailing Worker Logs

To watch a worker's output in real time:

```bash
tail -f .mahabharatha/logs/worker-w1.stderr.log
```

To see the last 50 lines of all worker error logs:

```bash
tail -50 .mahabharatha/logs/worker-*.stderr.log
```

### Searching Across Logs

Find a specific error across all worker logs:

```bash
grep -r "ImportError" .mahabharatha/logs/
```

Find when errors started occurring:

```bash
grep -n "ERROR\|FAILED\|Exception" .mahabharatha/logs/worker-*.stderr.log
```

### Interpreting Worker Logs

A healthy worker log follows this pattern:

```
[timestamp] Claimed task <task-id>
[timestamp] Starting execution...
[timestamp] Writing file: path/to/file.py
[timestamp] Running verification: python -m py_compile path/to/file.py
[timestamp] Verification passed
[timestamp] Task <task-id> completed
```

Warning signs to look for:

- **Repeated claim attempts** -- Worker cannot acquire a task. Check Task system sync.
- **Verification failures** -- Generated code does not pass its check. Look at the specific error.
- **Sudden termination** -- Log ends mid-task. Check for OOM kills or timeout.
- **"No tasks available"** -- Worker started but has nothing to do. Check level state and dependencies.

---

## Inspecting Task State

### Task System (Source of Truth)

The Claude Code Task system is the authoritative source for task state. When running inside a Claude Code session, use `/mahabharatha:status` to query it.

`/mahabharatha:status` cross-references the Task system with state JSON and flags any mismatches.

### State JSON (Supplementary)

State files live at `.mahabharatha/state/<feature>.json`. These are supplementary to the Task system.

To inspect the state file directly:

```bash
python -m json.tool .mahabharatha/state/<feature>.json
```

Key fields to check:

```json
{
  "current_level": 2,
  "paused": false,
  "tasks": {
    "task-1": { "status": "completed", "worker": "w1" },
    "task-2": { "status": "failed", "worker": "w2", "error": "..." },
    "task-3": { "status": "pending", "worker": null }
  }
}
```

### Task Graph

The task graph defines all tasks, their dependencies, files, and verification commands:

```bash
python -m json.tool .gsd/specs/<feature>/task-graph.json
```

Useful queries against the task graph:

```bash
# List all tasks and their levels
python -c "
import json
g = json.load(open('.gsd/specs/<feature>/task-graph.json'))
for t in g['tasks']:
    print(f\"L{t['level']} {t['id']}: {t['title']} -> deps: {t.get('dependencies', [])}\")"
```

```bash
# Find tasks that own a specific file
python -c "
import json
g = json.load(open('.gsd/specs/<feature>/task-graph.json'))
for t in g['tasks']:
    if 'path/to/file.py' in t.get('files', []):
        print(t['id'], t['title'])"
```

### Reconciling State Disagreements

If the Task system and state JSON disagree:

1. The Task system wins. It is the source of truth.
2. Run `/mahabharatha:kurukshetra --resume` to reconcile. This reads `TaskList` first and aligns state.
3. If manual intervention is needed, update the state JSON to match the Task system, not the other way around.

---

## Common Error Patterns

### Pattern: ImportError in generated code

**Symptom:** Task verification fails with `ModuleNotFoundError` or `ImportError`.

**Investigation:**
1. Check which module is missing from the error log.
2. Verify it is listed in project dependencies (`requirements.txt`, `package.json`).
3. Check if the import path matches the project structure.

**Resolution:** Install the missing dependency, or fix the import path in the task's context. Retry with `/mahabharatha:retry <task-id>`.

### Pattern: Multiple workers failing at the same level

**Symptom:** Several tasks at the same level fail simultaneously with different errors.

**Investigation:**
1. Check if they share a common dependency from a previous level.
2. Look for a failed merge that left the codebase in a broken state.
3. Run `/mahabharatha:debug` to get cross-worker correlation.

**Resolution:** Fix the upstream issue first (failed merge or broken dependency), then retry the level.

### Pattern: State corruption after crash

**Symptom:** `/mahabharatha:status` shows impossible state (e.g., tasks both completed and in-progress, negative counts).

**Investigation:**
1. Check `.mahabharatha/state/<feature>.json` for JSON syntax errors.
2. Compare against the Task system output.
3. Look for workers that were killed mid-write.

**Resolution:**
1. Back up the corrupted state file.
2. Run `/mahabharatha:kurukshetra --resume` to rebuild state from the Task system.
3. If the Task system is also inconsistent, manually reset affected tasks to `pending` and re-run.

### Pattern: Timeout with no error

**Symptom:** Worker stops producing output and eventually times out. No error in logs.

**Investigation:**
1. Check if the task is unusually large or complex.
2. Look at system resources (`top`, `df -h`).
3. Check if context engineering is enabled to reduce token usage.

**Resolution:** Break large tasks into smaller ones via `/mahabharatha:design`, or increase the timeout in `.mahabharatha/config.yaml`.

### Pattern: Merge quality gate failure

**Symptom:** Level advancement blocked because lint, typecheck, or test quality gates fail after merge.

**Investigation:**
1. Check the merge log for specific gate failures:
   ```bash
   cat .mahabharatha/logs/merge-*.log
   ```
2. Run the failing quality gate command manually to see full output.
3. Identify which worker's code introduced the failure.

**Resolution:** Fix the code that fails the quality gate. Run `/mahabharatha:merge` to re-attempt. If the quality gate command itself is wrong, update it in `.mahabharatha/config.yaml`.

---

## Advanced Diagnostics

### System-Level Checks

Run a deep diagnostic that covers infrastructure:

```
/mahabharatha:debug --deep
```

This checks:
- Git status and worktree health
- Disk space availability
- Docker daemon status and container state
- Port availability and conflicts
- Worktree integrity

### Environment Validation

Run environment diagnostics to verify the full toolchain:

```
/mahabharatha:debug --env
```

This checks:
- Python virtual environment and installed packages
- Docker installation and version
- System resources (CPU, memory, disk)
- `.mahabharatha/config.yaml` validation
- Claude Code configuration

### Generating a Full Report

To produce a comprehensive diagnostic report for sharing or review:

```
/mahabharatha:debug --deep --env --report claudedocs/full-diagnostic.md
```

The report includes all phases, evidence, hypotheses, and recommended actions in a single markdown document.

### Design Escalation

If `/mahabharatha:debug` determines that the issue is architectural (e.g., file ownership conflicts, missing tasks in the graph, incorrect dependency ordering), it will recommend running `/mahabharatha:design` to regenerate the task graph. The debug task subject will be annotated with "DESIGN ESCALATION" in this case.

---

## See Also

- [[Troubleshooting]] -- Quick problem/solution pairs for common issues
- [[Testing]] -- Running the test suite to validate fixes
- [[Command Reference]] -- Full syntax for all MAHABHARATHA commands
