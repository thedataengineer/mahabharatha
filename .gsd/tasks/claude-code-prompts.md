# MAHABHARATHA Implementation: Claude Code Prompts

Copy each prompt into Claude Code in sequence. Wait for completion before proceeding to next.

---

## SESSION 1

```
/sc:implement Implement MAHABHARATHA Level 1 Foundation tasks (Part 1).

Read specs: .gsd/specs/phase3/implementation_backlog.md, .gsd/specs/phase2/architecture_synthesis.md

Execute in order:

1. MAHABHARATHA-L1-001: Create mahabharatha/__init__.py (with __version__="0.1.0"), mahabharatha/py.typed, pyproject.toml (click>=8.0, pydantic>=2.0, pyyaml>=6.0, rich>=13.0), requirements.txt
   Verify: python -c "import mahabharatha; print(mahabharatha.__version__)"

2. MAHABHARATHA-L1-004: Create mahabharatha/constants.py with Level(IntEnum), TaskStatus(Enum), GateResult(Enum), WorkerStatus(Enum)
   Verify: python -c "from mahabharatha.constants import Level, TaskStatus, GateResult"

3. MAHABHARATHA-L1-006: Create mahabharatha/exceptions.py with MahabharathaError, ConfigurationError, TaskVerificationFailed, MergeConflict, WorkerError, GateFailure, WorktreeError
   Verify: python -c "from mahabharatha.exceptions import MahabharathaError, TaskVerificationFailed, MergeConflict"

4. MAHABHARATHA-L1-002: Create mahabharatha/types.py with TypedDict/dataclass: Task, TaskGraph, WorkerState, LevelStatus, GateConfig, MergeResult
   Verify: python -c "from mahabharatha.types import TaskGraph, WorkerState, LevelStatus"

Update .gsd/tasks/session-tracker.md marking these COMPLETE. --ultrathink
```

---

## SESSION 2

```
/sc:implement Implement MAHABHARATHA Level 1 Foundation tasks (Part 2).

Execute in order:

1. MAHABHARATHA-L1-003: Create mahabharatha/config.py with Pydantic models matching .mahabharatha/config.yaml structure. Include MahabharathaConfig.load() classmethod.
   Verify: python -c "from mahabharatha.config import MahabharathaConfig; c = MahabharathaConfig.load(); print(c.workers.max_concurrent)"

2. MAHABHARATHA-L1-007: Create mahabharatha/schemas/__init__.py, mahabharatha/schemas/task_graph.json (JSON Schema), mahabharatha/validation.py with validate_task_graph(), validate_file_ownership(), validate_dependencies()
   Verify: python -c "from mahabharatha.validation import validate_task_graph"

3. MAHABHARATHA-L1-005: Create mahabharatha/logging.py with get_logger(name, worker_id), setup_logging(), JsonFormatter for structured logs
   Verify: python -c "from mahabharatha.logging import get_logger; log = get_logger('test'); log.info('works')"

4. MAHABHARATHA-L1-008: Create mahabharatha/cli.py with Click group and stub subcommands: init, plan, design, kurukshetra, status, stop, retry, logs, merge, cleanup. Add entry point to pyproject.toml.
   Verify: python -m mahabharatha --help

Update .gsd/tasks/session-tracker.md marking Level 1 COMPLETE. --ultrathink
```

---

## SESSION 3

```
/sc:implement Implement MAHABHARATHA Level 2 Core tasks (Part 1).

Execute in order:

1. MAHABHARATHA-L2-001: Create mahabharatha/worktree.py with WorktreeManager class: create(), delete(), list_worktrees(), get_branch_name(), exists(). Use subprocess for git worktree commands.
   Verify: python -c "from mahabharatha.worktree import WorktreeManager; wm = WorktreeManager('.'); print(wm.list_worktrees())"

2. MAHABHARATHA-L2-002: Create mahabharatha/ports.py with PortAllocator class: allocate(), release(), is_available(). Use socket bind test for availability.
   Verify: python -c "from mahabharatha.ports import PortAllocator; pa = PortAllocator(); print(pa.allocate(5))"

3. MAHABHARATHA-L2-010: Create mahabharatha/git_ops.py with GitOps class: current_branch(), create_branch(), delete_branch(), merge(), rebase(), has_conflicts(), commit(), create_staging_branch()
   Verify: python -c "from mahabharatha.git_ops import GitOps; go = GitOps('.'); print(go.current_branch())"

Update .gsd/tasks/session-tracker.md marking these COMPLETE. --ultrathink
```

---

## SESSION 4

```
/sc:implement Implement MAHABHARATHA Level 2 Core tasks (Part 2).

Execute in order:

1. MAHABHARATHA-L2-004: Create mahabharatha/levels.py with LevelController class: start_level(), get_tasks_for_level(), mark_task_complete(), mark_task_failed(), is_level_complete(), can_advance(), advance_level(), get_status()
   Verify: python -c "from mahabharatha.levels import LevelController"

2. MAHABHARATHA-L2-003: Create mahabharatha/parser.py with TaskParser class: parse(), parse_dict(), get_task(), get_dependencies(), topological_sort(). Validate with mahabharatha.validation.
   Verify: python -c "from mahabharatha.parser import TaskParser"

3. MAHABHARATHA-L2-006: Create mahabharatha/gates.py with GateRunner class: run_gate(), run_all_gates(). Handle timeouts, capture stdout/stderr.
   Verify: python -c "from mahabharatha.gates import GateRunner"

4. MAHABHARATHA-L2-007: Create mahabharatha/verify.py with VerificationExecutor class: verify(), verify_task(). Return VerificationResult with success, exit_code, stdout, stderr, duration_ms.
   Verify: python -c "from mahabharatha.verify import VerificationExecutor"

Update .gsd/tasks/session-tracker.md marking these COMPLETE. --ultrathink
```

---

## SESSION 5

```
/sc:implement Implement MAHABHARATHA Level 2 Core tasks (Part 3).

Execute in order:

1. MAHABHARATHA-L2-005: Create mahabharatha/state.py with StateManager class: load(), save(), get_task_status(), set_task_status(), get_worker_state(), set_worker_state(), claim_task(), release_task(), append_event(). File-based with .mahabharatha/state/{feature}.json.
   Verify: python -c "from mahabharatha.state import StateManager"

2. MAHABHARATHA-L2-008: Create mahabharatha/assign.py with WorkerAssignment class: assign(), get_worker_tasks(), get_task_worker(), rebalance(). Balance tasks per level, respect file ownership.
   Verify: python -c "from mahabharatha.assign import WorkerAssignment"

3. MAHABHARATHA-L2-009: Create mahabharatha/containers.py with ContainerManager class: build(), start_worker(), stop_worker(), stop_all(), get_status(), get_logs(), health_check(), exec_in_worker(). Use docker/docker-compose.
   Verify: python -c "from mahabharatha.containers import ContainerManager"

Update .gsd/tasks/session-tracker.md marking Level 2 COMPLETE. --ultrathink
```

---

## SESSION 6

```
/sc:implement Implement MAHABHARATHA Level 3 Integration tasks (Part 1).

Execute in order:

1. MAHABHARATHA-L3-001: Create mahabharatha/orchestrator.py with Orchestrator class: start(), stop(), status(), _main_loop(), _start_level(), _on_level_complete(), _on_task_complete(), _spawn_worker(), _terminate_worker(). Coordinate LevelController, StateManager, ContainerManager, WorktreeManager.
   Verify: python -c "from mahabharatha.orchestrator import Orchestrator"

2. MAHABHARATHA-L3-002: Create mahabharatha/merge.py with MergeCoordinator class: prepare_merge(), run_pre_merge_gates(), execute_merge(), run_post_merge_gates(), finalize(), abort(), full_merge_flow().
   Verify: python -c "from mahabharatha.merge import MergeCoordinator"

3. MAHABHARATHA-L3-003: Create mahabharatha/worker_protocol.py with WorkerProtocol class: start(), claim_next_task(), execute_task(), report_complete(), report_failed(), check_context_usage(), should_checkpoint(), checkpoint_and_exit(). Exit codes: 0=done, 1=error, 2=checkpoint, 3=blocked.
   Verify: python -c "from mahabharatha.worker_protocol import WorkerProtocol"

Update .gsd/tasks/session-tracker.md marking these COMPLETE. --ultrathink
```

---

## SESSION 7

```
/sc:implement Implement MAHABHARATHA Level 3 Integration tasks (Part 2).

Execute in order:

1. MAHABHARATHA-L3-004: Create mahabharatha/commands/__init__.py and mahabharatha/commands/kurukshetra.py with Click command: kurukshetra(workers, feature, dry_run, resume). Load task graph, validate, create assignment, start orchestrator, display progress with rich. Update mahabharatha/cli.py to register.
   Verify: python -m mahabharatha kurukshetra --help

2. MAHABHARATHA-L3-005: Create mahabharatha/commands/status.py with Click command: status(feature, watch, json_output). Display progress, level breakdown, worker table with rich. Update mahabharatha/cli.py.
   Verify: python -m mahabharatha status --help

3. MAHABHARATHA-L3-006: Create mahabharatha/commands/stop.py with Click command: stop(feature, worker_id, force). Graceful checkpoint or force terminate. Update mahabharatha/cli.py.
   Verify: python -m mahabharatha stop --help

Update .gsd/tasks/session-tracker.md marking these COMPLETE. --ultrathink
```

---

## SESSION 8

```
/sc:implement Implement MAHABHARATHA Level 3 Integration tasks (Part 3).

Execute in order:

1. MAHABHARATHA-L3-007: Create mahabharatha/commands/retry.py with Click command: retry(task_id, feature, all_failed). Reset task status, clear assignment. Update mahabharatha/cli.py.
   Verify: python -m mahabharatha retry --help

2. MAHABHARATHA-L3-008: Create mahabharatha/commands/logs.py with Click command: logs(worker_id, feature, tail, follow, level). Stream from .mahabharatha/logs/ or container, colorize with rich. Update mahabharatha/cli.py.
   Verify: python -m mahabharatha logs --help

3. MAHABHARATHA-L3-009: Create mahabharatha/commands/cleanup.py with Click command: cleanup(feature, all_features, keep_logs, dry_run). Remove worktrees, branches, containers. Update mahabharatha/cli.py.
   Verify: python -m mahabharatha cleanup --help

Update .gsd/tasks/session-tracker.md marking Level 3 COMPLETE. --ultrathink
```

## SESSION 9

```
/sc:implement Implement MAHABHARATHA Level 4 Command tasks (Part 1).

Execute in order:

1. MAHABHARATHA-L4-001: Create mahabharatha/commands/init.py with detection logic for project type. Update .claude/commands/mahabharatha:init.md with complete prompt. Register in cli.py.
   Verify: python -m mahabharatha init --help

2. MAHABHARATHA-L4-002: Update .claude/commands/mahabharatha:plan.md with structured requirements template, APPROVED/REJECTED markers, example output.
   Verify: grep -q "APPROVED" .claude/commands/mahabharatha:plan.md

3. MAHABHARATHA-L4-003: Update .claude/commands/mahabharatha:design.md with task decomposition guidelines, file ownership rules, level criteria, task-graph.json schema.
   Verify: grep -q "task-graph.json" .claude/commands/mahabharatha:design.md

4. MAHABHARATHA-L4-004: Update .claude/commands/mahabharatha:kurukshetra.md with flag docs, worker-assignments.json format, progress display, resume instructions.
   Verify: grep -q "worker-assignments" .claude/commands/mahabharatha:kurukshetra.md

5. MAHABHARATHA-L4-005: Update .claude/commands/mahabharatha:status.md with output examples, watch mode, JSON schema, worker state meanings.
   Verify: grep -q "Progress:" .claude/commands/mahabharatha:status.md

Update .gsd/tasks/session-tracker.md marking these COMPLETE. --ultrathink
```

## SESSION 10

```
/sc:implement Implement MAHABHARATHA Level 4 Command tasks (Part 2).

Execute in order:

1. MAHABHARATHA-L4-006: Update .claude/commands/mahabharatha:worker.md with protocol spec, 70% context threshold, exit codes, task claiming, WIP commit format.
   Verify: grep -q "70%" .claude/commands/mahabharatha:worker.md

2. MAHABHARATHA-L4-007: Create mahabharatha/commands/merge_cmd.py with merge(feature, target, skip_gates, dry_run). Create .claude/commands/mahabharatha:merge.md. Register in cli.py.
   Verify: python -m mahabharatha merge --help

3. MAHABHARATHA-L4-008: Create .claude/commands/mahabharatha:logs.md with flag docs, log format, filtering examples.
   Verify: test -f .claude/commands/mahabharatha:logs.md

4. MAHABHARATHA-L4-009: Create .claude/commands/mahabharatha:stop.md with graceful vs force, checkpoint behavior, recovery.
   Verify: test -f .claude/commands/mahabharatha:stop.md

5. MAHABHARATHA-L4-010: Create .claude/commands/mahabharatha:cleanup.md with cleanup scope, dry-run usage, recovery.
   Verify: test -f .claude/commands/mahabharatha:cleanup.md

Update .gsd/tasks/session-tracker.md marking Level 4 COMPLETE. --ultrathink
```

## SESSION 11

```
/sc:implement Implement MAHABHARATHA Level 5 Quality tasks (Part 1).

Execute in order:

1. MAHABHARATHA-L5-001: Create tests/__init__.py, tests/conftest.py (fixtures: tmp_repo, sample_config, sample_task_graph, mock_container_manager), tests/test_config.py, tests/test_types.py. Add pytest to pyproject.toml.
   Verify: pytest tests/test_config.py -v

2. MAHABHARATHA-L5-002: Create tests/test_worktree.py, tests/test_levels.py, tests/test_gates.py, tests/test_git_ops.py with unit tests for each component.
   Verify: pytest tests/test_worktree.py tests/test_levels.py -v

Update .gsd/tasks/session-tracker.md marking these COMPLETE. --ultrathink
```

## SESSION 12

```
/sc:implement Implement MAHABHARATHA Level 5 Quality tasks (Part 2).

Execute in order:

1. MAHABHARATHA-L5-003: Create tests/integration/__init__.py, tests/integration/test_rush_flow.py (dry_run, single_level, multi_level, task_failure, checkpoint), tests/integration/test_merge_flow.py (clean, conflict, gate_failure).
   Verify: pytest tests/integration/ -v

2. MAHABHARATHA-L5-004: Create .mahabharatha/hooks/pre-commit (non-ASCII check, secrets check, commit message validation) and mahabharatha/security.py with check functions and install_hooks().
   Verify: bash .mahabharatha/hooks/pre-commit

3. MAHABHARATHA-L5-005: Update README.md with installation (pip install -e .), quick start, command reference. Update ARCHITECTURE.md with final component list and data flow.
   Verify: grep -q "pip install" README.md

Update .gsd/tasks/session-tracker.md marking Level 5 COMPLETE. --ultrathink
```

## SESSION 13: Final Verification

```
/sc:implement Run final verification for MAHABHARATHA implementation.

1. Run full test suite with coverage:
   pytest --cov=mahabharatha --cov-report=term-missing

2. Verify all CLI commands work:
   python -m mahabharatha --help
   python -m mahabharatha init --help
   python -m mahabharatha kurukshetra --help
   python -m mahabharatha status --help

3. Verify imports:
   python -c "from mahabharatha.orchestrator import Orchestrator; from mahabharatha.merge import MergeCoordinator; from mahabharatha.worker_protocol import WorkerProtocol"

4. Validate task graph schema:
   python -c "from mahabharatha.validation import validate_task_graph; import json; validate_task_graph(json.load(open('.gsd/tasks/task-graph.json')))"

5. Check documentation:
   test -f README.md && grep -q "pip install" README.md
   test -f ARCHITECTURE.md

Report final status and any failures. Update .gsd/tasks/session-tracker.md with IMPLEMENTATION COMPLETE. --ultrathink
```

---

## Quick Reference

| Session | Tasks | Focus |
|---------|-------|-------|
| 1 | L1-001, L1-002, L1-004, L1-006 | Package, types, constants, exceptions |
| 2 | L1-003, L1-005, L1-007, L1-008 | Config, logging, validation, CLI |
| 3 | L2-001, L2-002, L2-010 | Worktree, ports, git ops |
| 4 | L2-003, L2-004, L2-006, L2-007 | Parser, levels, gates, verify |
| 5 | L2-005, L2-008, L2-009 | State, assignment, containers |
| 6 | L3-001, L3-002, L3-003 | Orchestrator, merge, worker protocol |
| 7 | L3-004, L3-005, L3-006 | Kurukshetra, status, stop commands |
| 8 | L3-007, L3-008, L3-009 | Retry, logs, cleanup commands |
| 9 | L4-001 to L4-005 | Init, plan, design, kurukshetra, status prompts |
| 10 | L4-006 to L4-010 | Worker, merge, logs, stop, cleanup prompts |
| 11 | L5-001, L5-002 | Unit tests |
| 12 | L5-003, L5-004, L5-005 | Integration tests, security, docs |
| 13 | - | Final verification |
