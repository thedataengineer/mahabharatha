# Architecture: Module Reference

This page provides a complete reference of all Python modules in the `mahabharatha/` package. Modules are organized by functional area.

## Core Modules

| Module | Purpose | Key Classes / Functions |
|--------|---------|------------------------|
| `cli.py` | Click-based command-line interface. Registers all subcommands. | `cli` (click.Group) |
| `__init__.py` | Package initialization. Exports version and key constants. | `__version__` |
| `__main__.py` | Entry point for `python -m mahabharatha`. | -- |
| `constants.py` | Enumerations and constants used across the codebase. | `Level`, `TaskStatus`, `WorkerStatus`, `GateResult`, `MergeStatus` |
| `types.py` | TypedDict and dataclass definitions for structured data. | `Task`, `TaskGraph`, `FileSpec`, `VerificationSpec`, `WorkerState`, `FeatureMetrics` |
| `exceptions.py` | Exception hierarchy for all MAHABHARATHA error types. | `MahabharathaError`, `StateError`, `GitError`, `MergeConflictError`, `ValidationError`, `GateFailureError` |
| `config.py` | Pydantic-based configuration loaded from `.mahabharatha/config.yaml`. | `MahabharathaConfig`, `WorkersConfig`, `ProjectConfig`, `QualityGate`, `RulesConfig`, `EfficiencyConfig`, `LoopConfig`, `VerificationConfig`, `ModeConfig`, `MCPRoutingConfig`, `TDDConfig`, `ErrorRecoveryConfig` |
| `logging.py` | Structured JSON logging with worker context support. | `get_logger()` |

## Orchestration Modules

| Module | Purpose | Key Classes / Functions |
|--------|---------|------------------------|
| `orchestrator.py` | Central coordination engine. Delegates to extracted components for launcher setup, level transitions, retries, and state sync. | `Orchestrator` |
| `level_coordinator.py` | Manages level START, COMPLETE, and MERGE workflows. Triggers quality gates and branch merging at level boundaries. | `LevelCoordinator` |
| `worker_manager.py` | Worker lifecycle management: spawning, initialization, health monitoring, and termination. | `WorkerManager` |
| `task_retry_manager.py` | Retry logic with configurable backoff strategies. Tracks retry counts and enforces maximum attempts. | `TaskRetryManager` |
| `state_sync_service.py` | Synchronizes in-memory `LevelController` state with on-disk task state. Reassigns stranded tasks from stopped workers. | `StateSyncService` |
| `backpressure.py` | Monitors failure rates per level and applies backpressure (slowing or pausing) when thresholds are exceeded. | `BackpressureController`, `LevelPressure` |
| `circuit_breaker.py` | Prevents repeated spawning of workers that fail immediately. Implements open/half-open/closed circuit states. | `CircuitBreaker`, `CircuitState` |

## Execution Modules

| Module | Purpose | Key Classes / Functions |
|--------|---------|------------------------|
| `levels.py` | Level-based task execution control. Tracks task completion within levels and enforces level ordering. | `LevelController` |
| `assign.py` | Distributes tasks to workers. Balances load by estimated duration and respects level boundaries. | `WorkerAssignment` |
| `parser.py` | Parses `task-graph.json` and resolves dependencies. Validates structural integrity. | `TaskParser` |
| `validation.py` | Validation functions for task graphs, task IDs, file ownership, and dependency correctness. | `validate_task_graph()`, `validate_file_ownership()`, `validate_dependencies()` |
| `verify.py` | Runs task verification commands and captures results. Handles timeouts and failure reporting. | `TaskVerifier` |

## Worker Modules

| Module | Purpose | Key Classes / Functions |
|--------|---------|------------------------|
| `worker_main.py` | CLI entry point for worker subprocesses. Parses arguments and starts the worker protocol. | `parse_args()`, `main()` |
| `worker_protocol.py` | Implements the worker execution loop: load context, claim tasks, execute, verify, commit, report. | `WorkerProtocol` |
| `worker_metrics.py` | Per-worker metrics collection: task timing, context usage, resource consumption. | `WorkerMetrics` |
| `context_tracker.py` | Heuristic token counting and context threshold monitoring for checkpoint decisions. | `ContextTracker` |

## Infrastructure Modules

| Module | Purpose | Key Classes / Functions |
|--------|---------|------------------------|
| `launcher.py` | Abstract launcher interface and concrete implementations for subprocess and container backends. | `WorkerLauncher` (ABC), `SubprocessLauncher`, `ContainerLauncher`, `LauncherConfig`, `SpawnResult`, `WorkerHandle` |
| `launcher_configurator.py` | Launcher creation, auto-detection of backend type, and container lifecycle management. | `LauncherConfigurator` |
| `containers.py` | Docker container management: image building, health checks, volume mounts. | Container utilities |
| `git_ops.py` | Git branch management, merging, and rebasing operations. | `GitOps`, `BranchInfo` |
| `worktree.py` | Git worktree creation, listing, and cleanup for worker isolation. | `WorktreeManager`, `WorktreeInfo` |
| `ports.py` | Port allocation with availability checking and conflict avoidance. | `PortAllocator` |
| `command_executor.py` | Secure command execution with allowlisting, argument sanitization, and audit logging. Uses `shell=False`. | `CommandExecutor` |

## State and Persistence Modules

| Module | Purpose | Key Classes / Functions |
|--------|---------|------------------------|
| `state.py` | File-based state persistence with cross-process locking (`fcntl.flock`). Manages task status, worker state, and level completion. | `StateManager` |
| `task_sync.py` | One-way sync bridge from JSON state to Claude Code Tasks API. Loads design manifests for task registration. | `load_design_manifest()` |
| `spec_loader.py` | Loads feature specs (`requirements.md`, `design.md`) and formats them for worker prompt injection. | `SpecLoader`, `SpecContent` |
| `log_writer.py` | Structured JSONL log writer. Each worker writes to its own file. Thread-safe. | `StructuredLogWriter` |
| `log_aggregator.py` | Read-side log merging across all worker JSONL files by timestamp. No aggregated file on disk. | `LogAggregator`, `LogQuery` |

## Quality and Safety Modules

| Module | Purpose | Key Classes / Functions |
|--------|---------|------------------------|
| `gates.py` | Quality gate execution. Runs lint, typecheck, and test commands and captures pass/fail results. | `GateRunner` |
| `merge.py` | Merge coordination for level completion. Orchestrates branch merging, conflict detection, and gate execution. | `MergeFlowResult` |
| `security.py` | Security utilities: secret detection patterns, file permission checks. | Secret pattern matching |
| `security_rules.py` | Fetches and integrates secure coding rules based on detected project languages. | Rule fetching and filtering |
| `risk_scoring.py` | Per-task risk assessment, critical path identification, and overall risk grading. | Risk scoring functions |
| `preflight.py` | Pre-flight checks before kurukshetra: Docker, auth, ports, disk space, git worktree support. | `CheckResult` |

## Cross-Cutting Capability Modules

| Module | Purpose | Key Classes / Functions |
|--------|---------|------------------------|
| `depth_tiers.py` | 5-tier analysis depth control (quick → ultrathink). Maps CLI flags to token budgets and MCP server recommendations. | `DepthTier` (enum), `DepthRouter`, `DepthConfig` |
| `efficiency.py` | Token efficiency with 3 context zones (green/yellow/red). Auto-triggers compact mode at configurable threshold. | `EfficiencyZone` (enum), `ZoneDetector`, `CompactFormatter`, `EfficiencyConfig` |
| `modes.py` | 5 behavioral modes (precision/speed/exploration/refactor/debug) with keyword auto-detection from task descriptions. | `BehavioralMode` (enum), `ModeDetector`, `ModeConfig` |
| `mcp_router.py` | Capability-based MCP server selection. Matches task keywords to server capabilities with cost-aware ranking. | `MCPRouter`, `MCPRoutingConfig`, `ServerCapability`, `RoutingDecision` |
| `mcp_telemetry.py` | Records MCP routing decisions for analysis. Tracks server selection frequency and latency. | `RoutingTelemetry`, `RoutingRecord` |
| `verification_gates.py` | Verification pipeline with artifact storage and staleness detection. Re-runs gates older than configurable threshold. | `GatePipeline`, `VerificationConfig`, `GateArtifact` |
| `loops.py` | Convergence-based iterative improvement cycles. Stops on plateau or regression with optional rollback. | `LoopController`, `IterationResult`, `LoopConfig` |
| `tdd.py` | TDD enforcement protocol. Validates red-green-refactor order and detects anti-patterns (mock-heavy, no-assertions). | `TDDProtocol`, `TestFirstValidator`, `TDDConfig` |
| `rules/` | Engineering rules framework. Loads YAML rules from `.mahabharatha/rules/`, filters by file extension, injects into worker context. | `RuleLoader`, `RuleValidator`, `RuleInjector`, `RulesConfig` |

## Plugin and Extension Modules

| Module | Purpose | Key Classes / Functions |
|--------|---------|------------------------|
| `plugins.py` | Plugin system with ABCs and registry for quality gates, lifecycle hooks, and custom launchers. | `PluginRegistry`, `GateContext`, `ContextPlugin` (ABC) |
| `plugin_config.py` | Pydantic configuration models for plugins: hooks, gates, context engineering. | `PluginsConfig`, `ContextEngineeringConfig`, `HookConfig`, `PluginGateConfig` |
| `context_plugin.py` | Context engineering plugin. Combines security rule filtering, spec context, and command splitting to minimize token usage. | `ContextEngineeringPlugin` |
| `command_splitter.py` | Splits large command files (over 300 lines) into `.core.md` and `.details.md` for token efficiency. | `CommandSplitter` |

## Planning and Analysis Modules

| Module | Purpose | Key Classes / Functions |
|--------|---------|------------------------|
| `dryrun.py` | Dry-run simulation. Validates everything a real kurukshetra would, shows timeline estimates and worker balance. | `DryRunResult`, `LevelTimeline` |
| `whatif.py` | What-if analysis comparing different worker counts and execution modes. | What-if comparison engine |
| `metrics.py` | Metrics computation for workers and tasks: durations, throughput, success rates. | Metrics aggregation |
| `render_utils.py` | Shared Rich rendering components for status and dry-run displays. | Rendering helpers |

## Inception Mode Modules

| Module | Purpose | Key Classes / Functions |
|--------|---------|------------------------|
| `inception.py` | Inception Mode orchestration: requirements gathering, tech selection, project scaffolding. | Inception workflow |
| `charter.py` | Project charter: conversational requirements gathering and `PROJECT.md` generation. | `ProjectCharter`, `gather_requirements()` |
| `tech_selector.py` | Technology stack recommendation and interactive selection for new projects. | Technology selection UI |
| `devcontainer_features.py` | Dynamic devcontainer generation with multi-language runtime support. | Devcontainer feature generation |

## Utility Modules

| Module | Purpose | Key Classes / Functions |
|--------|---------|------------------------|
| `retry_backoff.py` | Backoff delay calculation for task retries (exponential, linear, jitter). | `RetryBackoffCalculator` |
| `backlog.py` | Generates markdown backlog files from task graph data. | Backlog generation |

## Command Modules (`mahabharatha/commands/`)

Each file in `mahabharatha/commands/` implements a Click subcommand registered in `cli.py`.

| Module | Command | Purpose |
|--------|---------|---------|
| `init.py` | `mahabharatha init` | Initialize MAHABHARATHA infrastructure in a project |
| `plan.py` | `mahabharatha plan` | Capture feature requirements |
| `design.py` | `mahabharatha design` | Generate architecture and task graph |
| `kurukshetra.py` | `mahabharatha kurukshetra` | Launch parallel worker execution |
| `status.py` | `mahabharatha status` | Monitor execution progress |
| `merge_cmd.py` | `mahabharatha merge` | Trigger manual merge operations |
| `stop.py` | `mahabharatha stop` | Stop running workers |
| `retry.py` | `mahabharatha retry` | Retry failed tasks |
| `logs.py` | `mahabharatha logs` | View aggregated worker logs |
| `cleanup.py` | `mahabharatha cleanup` | Remove worktrees and state files |
| `build.py` | `mahabharatha build` | Build project artifacts |
| `test_cmd.py` | `mahabharatha test` | Run project tests |
| `review.py` | `mahabharatha review` | Code review utilities |
| `analyze.py` | `mahabharatha analyze` | Codebase analysis |
| `refactor.py` | `mahabharatha refactor` | Refactoring operations |
| `debug.py` | `mahabharatha debug` | Debugging utilities |
| `document.py` | `mahabharatha document` | Documentation generation |
| `wiki.py` | `mahabharatha wiki` | Wiki management |
| `git_cmd.py` | `mahabharatha git` | Git helper operations |
| `tdd.py` | `mahabharatha tdd` | TDD enforcement commands (status, reset) |
| `security_rules_cmd.py` | `mahabharatha security-rules` | Security rule management |
| `install_commands.py` | `mahabharatha install-commands` | Install slash commands |

## Related Pages

- [[Architecture-Overview]] -- High-level architecture and core concepts.
- [[Architecture-Execution-Flow]] -- Step-by-step execution lifecycle.
- [[Architecture-Dependency-Graph]] -- Module import relationships visualized.
