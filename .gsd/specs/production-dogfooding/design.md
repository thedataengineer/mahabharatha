# Design: production-dogfooding

## Overview

Two deliverables built across 4 levels (20 tasks):

1. **E2E Test Harness** — MockWorker + E2EHarness for CI-safe and real-mode pipeline testing
2. **Plugin System** — ABCs, registry, config models, integration into orchestrator/worker/gates/launcher

MAHABHARATHA dogfoods itself: the plugin system is built by MAHABHARATHA executing a 20-task graph.

## Architecture

```
Level 1 (foundation)     Level 2 (core)            Level 3 (integration)      Level 4 (testing)
┌───────────────────┐    ┌───────────────────┐     ┌───────────────────────┐   ┌──────────────────────┐
│ MockWorker        │───▶│ E2E conftest      │     │ Orchestrator hooks    │   │ Plugin lifecycle     │
│ E2EHarness        │───▶│ Full pipeline test │     │ Worker hooks          │   │ Dogfood E2E test     │
│ Plugin ABCs       │───▶│ Plugin unit tests  │───▶ │ GateRunner hooks      │──▶│ Pytest markers       │
│ Config models     │───▶│ Config unit tests  │     │ Launcher plugin       │   │ Plugin docs          │
│ HookEvent enum    │    │ MahabharathaConfig integr. │     │ Real execution test   │   │ Bug tracking         │
└───────────────────┘    └───────────────────┘     └───────────────────────┘   └──────────────────────┘
```

## Component Breakdown

### E2E Test Harness

| Component | File | Purpose |
|-----------|------|---------|
| MockWorker | `tests/e2e/mock_worker.py` | Patches `invoke_claude_code` with deterministic pathlib file ops |
| E2EHarness | `tests/e2e/harness.py` | Sets up real git repo, writes task-graph.json, runs Orchestrator |
| E2EResult | `tests/e2e/harness.py` | Dataclass: success, tasks_completed/failed, levels, merges, duration |
| Fixtures | `tests/e2e/conftest.py` | e2e_harness, mock_worker, sample_task_graph, e2e_repo |

**Data flow**: E2EHarness.setup_repo() → setup_task_graph(tasks) → setup_config() → run(workers=N) → E2EResult

**Modes**:
- `mock` — patches invoke_claude_code with MockWorker (CI-safe, no API key)
- `real` — uses actual Claude CLI (requires auth, gated by `@pytest.mark.real_e2e`)

### Plugin System

| Component | File | Purpose |
|-----------|------|---------|
| QualityGatePlugin | `mahabharatha/plugins.py` | ABC: `run(ctx: GateContext) -> GateRunResult` |
| LifecycleHookPlugin | `mahabharatha/plugins.py` | ABC: `on_event(event: LifecycleEvent) -> None` |
| LauncherPlugin | `mahabharatha/plugins.py` | ABC: `create_launcher(config) -> WorkerLauncher` |
| PluginRegistry | `mahabharatha/plugins.py` | Register/emit/run hooks, gates, launchers |
| LifecycleEvent | `mahabharatha/plugins.py` | Dataclass: event_type, data dict, timestamp |
| GateContext | `mahabharatha/plugins.py` | Dataclass: feature, level, cwd, config |
| Config models | `mahabharatha/plugin_config.py` | Pydantic: HookConfig, PluginGateConfig, PluginsConfig |
| PluginHookEvent | `mahabharatha/constants.py` | Enum: 8 lifecycle event types (already exists) |

**Plugin loading**:
1. YAML config → `PluginRegistry.load_yaml_hooks(hooks_config)` → shell command hooks
2. Entry points → `PluginRegistry.load_entry_points('mahabharatha.plugins')` → Python plugins

**Event flow**:
```
Orchestrator._spawn_worker()  → emit(WORKER_SPAWNED)
Worker.execute_task()         → emit(TASK_STARTED) → execute → emit(TASK_COMPLETED)
Orchestrator._on_level_done() → emit(LEVEL_COMPLETE) → merge → emit(MERGE_COMPLETE)
Orchestrator._main_loop_exit  → emit(RUSH_FINISHED)
GateRunner.run_all_gates()    → emit(QUALITY_GATE_RUN) + run_plugin_gates()
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Security model | Read-only state views + timeouts | Plugins cannot mutate orchestrator state; timeout prevents hangs |
| Hook exceptions | Per-hook try/except, never crash | Faulty plugin must not halt kurukshetra |
| Plugin discovery | YAML + entry_points | Simple hooks via config, complex plugins via Python packages |
| Gate integration | Plugin gates run after config gates | Preserves existing gate ordering, plugins are additive |
| Launcher plugins | Checked before builtin fallback | `subprocess`/`container` always available as fallback |
| Plugin registry | Optional parameter | All existing code paths work unchanged when no plugins configured |

## File Ownership Matrix

### Level 1 — Foundation (5 tasks, parallel)
| Task ID | Creates | Modifies |
|---------|---------|----------|
| DF-L1-001 | `tests/e2e/mock_worker.py` | — |
| DF-L1-002 | `tests/e2e/harness.py` | — |
| DF-L1-003 | `mahabharatha/plugins.py` | — |
| DF-L1-004 | `mahabharatha/plugin_config.py` | — |
| DF-L1-005 | — | `mahabharatha/constants.py` |

### Level 2 — Core (5 tasks, parallel)
| Task ID | Creates | Modifies |
|---------|---------|----------|
| DF-L2-001 | `tests/e2e/conftest.py` | — |
| DF-L2-002 | `tests/e2e/test_full_pipeline.py` | — |
| DF-L2-003 | `tests/unit/test_plugins.py` | — |
| DF-L2-004 | `tests/unit/test_plugin_config.py` | — |
| DF-L2-005 | — | `mahabharatha/config.py` |

### Level 3 — Integration (5 tasks, parallel)
| Task ID | Creates | Modifies |
|---------|---------|----------|
| DF-L3-001 | — | `mahabharatha/orchestrator.py` |
| DF-L3-002 | — | `mahabharatha/worker_protocol.py` |
| DF-L3-003 | — | `mahabharatha/gates.py` |
| DF-L3-004 | — | `mahabharatha/launcher.py` |
| DF-L3-005 | `tests/e2e/test_real_execution.py` | — |

### Level 4 — Testing (5 tasks, parallel)
| Task ID | Creates | Modifies |
|---------|---------|----------|
| DF-L4-001 | `tests/integration/test_plugin_lifecycle.py` | — |
| DF-L4-002 | `tests/e2e/test_dogfood_plugin.py` | — |
| DF-L4-003 | — | `pyproject.toml` |
| DF-L4-004 | `mahabharatha/data/commands/mahabharatha:plugins.md` | — |
| DF-L4-005 | `claudedocs/dogfood-bugs.md` | — |

**No file conflicts within any level.** Each task owns distinct files.

## Dependency Graph

```
L1-001 ──┐
          ├──▶ L2-001 ──▶ L2-002 ──▶ L3-005 ──▶ L4-003
L1-002 ──┘                                │
                                           └──▶ L4-002
L1-003 ──┬──▶ L2-003 ──┬──▶ L3-001 ──┬──▶ L4-001
          │              │              │
L1-005 ──┘              │   L3-002 ──┘
                         │              │
                         ├──▶ L3-003 ──┤
                         │              │
                         └──▶ L3-004 ──┴──▶ L4-004
                                        │
L1-004 ──┬──▶ L2-004                    └──▶ L4-002
          └──▶ L2-005 ──┘

L4-005 has no dependencies (standalone)
```

## Testing Strategy

| Layer | Tests | Runner |
|-------|-------|--------|
| Unit | test_plugins.py, test_plugin_config.py | `pytest tests/unit/ -v` |
| Integration | test_plugin_lifecycle.py | `pytest tests/integration/ -v` |
| E2E (mock) | test_full_pipeline.py, test_dogfood_plugin.py | `pytest tests/e2e/ -v -m "not real_e2e"` |
| E2E (real) | test_real_execution.py | `pytest tests/e2e/ -v -m real_e2e` (requires auth) |

**Regression**: Full existing test suite (4874+ tests) must pass after all changes.

## Verification

Each task has a verification command in task-graph.json. Tasks pass when:
1. Verification command exits 0
2. All acceptance criteria met
3. No regressions in existing tests for modified files
