# Mahabharatha

Parallel Claude Code execution system. Overwhelm features with coordinated mahabharathaling instances.

## Quick Start

These are Claude Code slash commands. Use them inside a Claude Code session:

```claude
/mahabharatha:init               # Set up project infrastructure
/mahabharatha:brainstorm         # Discover what to build (optional)
/mahabharatha:plan user-auth     # Plan a feature
/mahabharatha:design             # Design architecture (after approval)
/mahabharatha:Kurukshetra --workers=5   # Launch the Akshauhini (after approval)
/mahabharatha:status             # Monitor progress
```

## How It Works

1. **Plan**: You describe what to build. Mahabharatha captures requirements.
2. **Design**: Mahabharatha creates architecture and breaks work into atomic tasks with exclusive file ownership.
3. **Kurukshetra**: Multiple Claude Code instances execute tasks in parallel, organized by dependency levels.
4. **Merge**: Orchestrator merges branches after each level, runs quality gates.

## Key Concepts

**Levels**: Tasks grouped by dependencies. All mahabharathalings finish Level 1 before any start Level 2.

**File Ownership**: Each task owns specific files. No conflicts possible.

**Spec as Memory**: Warriors read spec files, not conversation history. Stateless and restartable.

**Verification**: Every task has an automated verification command. Pass or fail, no subjectivity.

## Claude Code Task Ecosystem (MANDATORY — READ THIS FIRST)

> **This section has been rearchitected before due to drift. Pay close attention.**

**The Claude Code Task system is the authoritative backbone for all Mahabharatha task state.** Every Mahabharatha command MUST use Claude Code Tasks (TaskCreate, TaskUpdate, TaskList, TaskGet) for tracking work. This is non-negotiable.

### Core Rules

1. **Tasks are the source of truth.** State JSON files (`.mahabharatha/state/`) are supplementary. If Task system and state JSON disagree, the Task system wins.
2. **Every command tracks itself.** All `/mahabharatha:*` commands must TaskCreate on start, TaskUpdate to `in_progress`, and TaskUpdate to `completed` on finish.
3. **Workers claim via Tasks.** Before executing a Mahabharatha task, workers MUST call TaskUpdate with `status: "in_progress"`. After completion or failure, update accordingly.
4. **Dependencies use Task fields.** Use `blocks`/`blockedBy` via TaskUpdate — not just task-graph.json.
5. **Sessions share via CLAUDE_CODE_TASK_LIST_ID.** Workers inherit the orchestrator's `CLAUDE_CODE_TASK_LIST_ID` by default. If the orchestrator has no value set, workers use the same default task list. Teams can explicitly `export CLAUDE_CODE_TASK_LIST_ID=feature` before starting Claude Code for feature-scoped lists.
6. **Tasks persist in `~/.claude/tasks/`.** They survive session restarts. They are the coordination mechanism between parallel Claude Code instances.
7. **Resume checks existing Tasks.** `/mahabharatha:Kurukshetra --resume` calls TaskList first and only creates tasks that don't already exist.

### Task Subject Convention

All Mahabharatha tasks use bracketed prefixes for discoverability:
- `[Plan] Capture requirements: {feature}`
- `[Design] Architecture for {feature}`
- `[L{level}] {task title}` — execution tasks from task-graph.json
- `[Brainstorm] Discovery: {domain}`
- `[Init]`, `[Cleanup]`, `[Review]`, `[Build]`, `[Test]`, `[Security]`, etc. — utility commands

### Why This Matters

Without Task ecosystem integration, parallel workers can't coordinate, sessions lose state on restart, and `/mahabharatha:status` has no authoritative data source. The Task system IS the project management layer for Mahabharatha.

### Anti-Drift Rules

**This system has drifted before. These rules exist to prevent it from happening again.**

1. **Never remove Task tool calls from command files.** If a command file references TaskCreate, TaskUpdate, TaskList, or TaskGet, those references are load-bearing. Do not remove, comment out, or "simplify" them.

2. **Every command file MUST contain Task tool calls.** All command files in `mahabharatha/data/commands/` are required to have Task ecosystem integration. There are zero exceptions. The minimum pattern for any command is:
   ```
   On invocation:  TaskCreate (subject with bracketed prefix)
   Immediately:    TaskUpdate status "in_progress"
   On completion:  TaskUpdate status "completed"
   ```

3. **Backbone commands have additional requirements.** These 5 files have deeper integration beyond the minimum pattern. Do not reduce them to the minimum:
   - `worker.md` — TaskUpdate to claim tasks, TaskUpdate for failures/checkpoints, TaskList at completion
   - `status.md` — TaskList as primary data source, cross-reference with state JSON, flag mismatches
   - `merge.md` — TaskUpdate after quality gates per level, TaskList verification at finalize
   - `stop.md` — TaskUpdate with PAUSED/FORCE STOPPED annotations
   - `retry.md` — TaskGet to read state, TaskUpdate to reset to pending, TaskUpdate on reassignment

4. **State JSON is the fallback, not the primary.** If you find yourself writing code that reads `.mahabharatha/state/` without also consulting TaskList, you are drifting. State JSON supplements Tasks, not the other way around.

5. **New commands get Task integration on creation.** If you create a new `/mahabharatha:*` command file, it MUST include the minimum Task tracking pattern before it is considered complete.

6. **Every new module must have a production caller.** If a PR creates a new `.py` file in `mahabharatha/`, at least one other production file must import it. Test-only imports don't count. Standalone entry points (`__main__.py`, files with `if __name__`) are exempt. Run `python -m mahabharatha.validate_commands` to check.

7. **Every new module must have an integration test.** Unit tests prove the module works in isolation. Integration tests prove it works with its callers. A module with unit tests but no integration test is incomplete. Design-phase `consumers` field tracks who calls what.

### Drift Detection Checklist

Run this check when modifying any Mahabharatha command file. If any check fails, fix it before committing.

```bash
# 1. All  command files must reference Task tools (exclude .core.md/.details.md)
grep -rL "TaskCreate\|TaskUpdate\|TaskList\|TaskGet" mahabharatha/data/commands/*.md | grep -v '\.core\.md\|\.details\.md'
# Expected output: (empty — no files missing Task references)

# 2. Backbone files must have deeper integration
for f in worker status merge stop retry; do
  count=$(grep -c "TaskUpdate\|TaskList\|TaskGet" "mahabharatha/data/commands/$f.md")
  echo "$f.md — $count Task references (expect ≥3)"
done

# 3. No command file should reference state JSON without also referencing TaskList
for f in mahabharatha/data/commands/*.md; do
  has_state=$(grep -c "state.*json\|STATE_FILE\|\.mahabharatha/state" "$f")
  has_tasks=$(grep -c "TaskList\|TaskGet" "$f")
  if [ "$has_state" -gt 0 ] && [ "$has_tasks" -eq 0 ]; then
    echo "DRIFT: $f reads state JSON but has no TaskList/TaskGet"
  fi
done

# 4. CLAUDE_CODE_TASK_LIST_ID in launcher allowlist
grep -q "CLAUDE_CODE_TASK_LIST_ID" mahabharatha/launcher.py || echo "DRIFT: missing from ALLOWED_ENV_VARS"

# 5. All spawn methods conditionally inject CLAUDE_CODE_TASK_LIST_ID
count=$(grep -c "CLAUDE_CODE_TASK_LIST_ID" mahabharatha/launcher.py)
echo "launcher.py — $count CLAUDE_CODE_TASK_LIST_ID refs (expect ≥4)"

# 6. No orphaned modules (zero production imports)
python -m mahabharatha.validate_commands  # includes module wiring check

# 7. New modules have integration tests
for f in $(git diff --name-only --diff-filter=A HEAD~1 -- 'mahabharatha/*.py'); do
  stem=$(basename "$f" .py)
  if ! find tests/integration -name "*${stem}*" 2>/dev/null | grep -q .; then
    echo "DRIFT: $f has no integration test"
  fi
done
```

**Automated:** Run `python -m mahabharatha.validate_commands` to execute all drift checks programmatically. Use `--auto-split` to fix oversized files automatically. This runs in CI and pre-commit.

### What Drift Looks Like

Watch for these patterns — they are symptoms of drift:

- **"Simplified" commands** — Someone removes Task calls to make a command file shorter or "cleaner." The Task calls are not boilerplate; they are coordination infrastructure.
- **State JSON as primary** — Code that reads/writes `.mahabharatha/state/` and skips the Task system entirely. State JSON is a cache, not the source of truth.
- **Missing subject prefixes** — Tasks created without `[Bracketed]` prefixes break discoverability for `/mahabharatha:status` and `/mahabharatha:cleanup`.
- **Workers not claiming tasks** — If workers execute tasks without calling TaskUpdate(in_progress), other workers and the orchestrator have no visibility.
- **New commands without tracking** — A new `/mahabharatha:*` command that lacks TaskCreate/TaskUpdate is incomplete, even if it "works."
- **TaskCreate without lifecycle** — Creating a task but never updating it to in_progress or completed is worse than not creating it (it pollutes the task list with stale entries).
- **Unwired modules** — A PR delivers new `.py` files with unit tests but no production callers. The module "works" in isolation but is never called. Classic symptom: CLI flags parsed but never consumed, config sections defined but never read. Run `python -m mahabharatha.validate_commands` to detect.

**If you are modifying any Mahabharatha command file and it lacks Task tool calls, add them.** Do not create or modify Mahabharatha commands without Task ecosystem integration.

## Container Execution (Non-Negotiable)

When a user specifies `--mode container` or says "containerize", workers MUST run in Docker containers. Never substitute with manual edits or subprocess mode. Container mode is a first-class execution path, not a fallback.

### Authentication Methods

Container workers authenticate via two methods:

- **OAuth**: Mount `~/.claude` into container (Claude Pro/Team accounts)
- **API Key**: Pass `ANTHROPIC_API_KEY` env var into container

Both are implemented in `mahabharatha/launcher.py:684-8`. This is settled infrastructure — do not reimplement or bypass.

## Cross-Cutting Capabilities

Mahabharatha includes 8 cross-cutting capabilities controlled via CLI flags and config:

| Capability | CLI Flag | Config Section |
|------------|----------|---------------|
| Analysis Depth Tiers | `--quick/--think/--think-hard/--ultrathink` | — |
| Token Efficiency | `--no-compact` (ON by default) | `efficiency` |
| Behavioral Modes | `--mode` | `behavioral_modes` |
| MCP Auto-Routing | `--mcp/--no-mcp` | `mcp_routing` |
| Engineering Rules | — | `rules` |
| Improvement Loops | `--no-loop/--iterations` (ON by default) | `improvement_loops` |
| Verification Gates | — | `verification` |
| TDD Enforcement | `--tdd` | `tdd` |

These integrate with the context engineering plugin to inject rules, MCP hints, and mode-specific behavior into worker prompts.

## Configuration

Edit `.mahabharatha/config.yaml` for:
- Warrior limits
- Timeouts
- Quality gate commands
- MCP servers
- Resource limits
- Cross-cutting capabilities (rules, efficiency, modes, verification, TDD, etc.)

## Context Engineering

Mahabharatha includes a context engineering plugin that minimizes token usage across workers through three subsystems:

### Command Splitting

Large command files (>300 lines) are split into `.core.md` (essential instructions, ~30%) and `.details.md` (reference material, ~70%). The original file retains core content for backward compatibility.

Split files: brainstorm, init, design, Kurukshetra, plugins, debug, plan, worker, merge, status.

### Task-Scoped Context

Each task in task-graph.json can include a `context` field with scoped content:
- Security rules filtered by file extension (.py → Python rules, .js → JavaScript rules)
- Spec excerpts relevant to the task's description and files
- Dependency context from upstream tasks

Workers use task-scoped context instead of loading full spec files, saving ~2000-5000 tokens per task.

### Configuration

```yaml
# .mahabharatha/config.yaml
plugins:
  context_engineering:
    enabled: true
    command_splitting: true
    security_rule_filtering: true
    task_context_budget_tokens: 4000
    fallback_to_full: true
```

### Monitoring

Use `/mahabharatha:status` to view the CONTEXT BUDGET section showing:
- Split command count and token savings
- Per-task context population rate
- Security rule filtering stats

## Documentation Impact Analysis

The `/z:plan` command now includes Section 11 "Documentation Impact Analysis" in its requirements template. This ensures every feature plan explicitly identifies which docs need updating. The `/z:design` command mandates CHANGELOG.md and documentation update tasks in every task graph.

## PR Documentation Rules

When creating a pull request, **always update CHANGELOG.md** under the `[Unreleased]` section with a brief entry describing the change. Use the appropriate category:

- **Added** — new features or capabilities
- **Changed** — modifications to existing functionality
- **Fixed** — bug fixes
- **Removed** — removed features or deprecated code

If the PR is trivial (typo fix, CI config, test-only), apply the `skip-changelog` label instead. A CI check enforces this — PRs without a CHANGELOG update or the `skip-changelog` label will fail.

## Troubleshooting

Warriors not starting? Check Docker, ANTHROPIC_API_KEY, and port availability.

Tasks failing? Check verification commands in task-graph.json.

Need to restart? Mahabharatha is crash-safe. Run `/mahabharatha:Kurukshetra` again to resume.

<!-- SECURITY_RULES_START -->
# Security Rules

Auto-generated from [TikiTribe/claude-secure-coding-rules](https://github.com/TikiTribe/claude-secure-coding-rules)

## Detected Stack

- **Languages**: javascript, python
- **Infrastructure**: docker

## Fetched Rules

- `_core/owasp-2025.md`
- `containers/docker/CLAUDE.md`
- `languages/javascript/CLAUDE.md`
- `languages/python/CLAUDE.md`

<!-- SECURITY_RULES_END -->

## CI/CD Debugging section

When asked to check CI/test failures, always fetch GitHub Actions logs first rather than running tests locally unless explicitly requested.

## Workflow Execution section

Before executing any plan file, verify the plan's actual purpose matches the requested task by reading the plan file contents first.


## Custom Workflows section

When invoking custom commands like /z:plan, /z:design, or /mahabharatha workflows, confirm the intended scope and dependencies before beginning parallel execution.
