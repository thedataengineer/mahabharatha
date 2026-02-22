"""E2E test for MAHABHARATHA dogfooding: plugin system build via MAHABHARATHA orchestration.

This test validates that MAHABHARATHA can orchestrate the plugin system build end-to-end
using the actual 20-task graph from the production-dogfooding design.
"""

from __future__ import annotations

from tests.e2e.harness import E2EHarness


def _plugin_task_graph() -> list[dict]:
    """Build the 20-task plugin system task graph from production-dogfooding design.

    Returns task list matching the production-dogfooding design with:
    - Level 1: Foundation (5 tasks) - MockWorker, E2EHarness, Plugin ABCs, Config, HookEvent
    - Level 2: Core (5 tasks) - E2E conftest, pipeline test, plugin tests, config, MahabharathaConfig
    - Level 3: Integration (5 tasks) - Orchestrator hooks, worker hooks, gate hooks, launcher
    - Level 4: Testing (5 tasks) - Plugin lifecycle, dogfood E2E, pytest markers, docs

    Returns:
        List of 20 task dictionaries with dependencies, files, and verification commands.
    """
    return [
        # ===== Level 1: Foundation (5 tasks, parallel) =====
        {
            "id": "DF-L1-001",
            "title": "Create MockWorker",
            "description": "Create tests/e2e/mock_worker.py with MockWorker class.",
            "phase": "foundation",
            "level": 1,
            "dependencies": [],
            "files": {
                "create": ["tests/e2e/mock_worker.py"],
                "modify": [],
                "read": [],
            },
            "verification": {
                "command": "python -c 'from tests.e2e.mock_worker import MockWorker'",
                "timeout_seconds": 30,
            },
        },
        {
            "id": "DF-L1-002",
            "title": "Create E2EHarness",
            "description": "Create tests/e2e/harness.py with E2EHarness class.",
            "phase": "foundation",
            "level": 1,
            "dependencies": [],
            "files": {
                "create": ["tests/e2e/harness.py"],
                "modify": [],
                "read": [],
            },
            "verification": {
                "command": "python -c 'from tests.e2e.harness import E2EHarness, E2EResult'",
                "timeout_seconds": 30,
            },
        },
        {
            "id": "DF-L1-003",
            "title": "Create plugin ABCs",
            "description": "Create mahabharatha/plugins.py with plugin ABCs and PluginRegistry.",
            "phase": "foundation",
            "level": 1,
            "dependencies": [],
            "files": {
                "create": ["mahabharatha/plugins.py"],
                "modify": [],
                "read": [],
            },
            "verification": {
                "command": "python -c 'from mahabharatha.plugins import PluginRegistry'",
                "timeout_seconds": 30,
            },
        },
        {
            "id": "DF-L1-004",
            "title": "Create plugin config models",
            "description": "Create mahabharatha/plugin_config.py with Pydantic config models.",
            "phase": "foundation",
            "level": 1,
            "dependencies": [],
            "files": {
                "create": ["mahabharatha/plugin_config.py"],
                "modify": [],
                "read": [],
            },
            "verification": {
                "command": (
                    "python -c 'from mahabharatha.plugin_config import HookConfig, PluginGateConfig, PluginsConfig'"
                ),
                "timeout_seconds": 30,
            },
        },
        {
            "id": "DF-L1-005",
            "title": "Add PluginHookEvent enum",
            "description": "Add PluginHookEvent enum to mahabharatha/constants.py with 8 lifecycle event types.",
            "phase": "foundation",
            "level": 1,
            "dependencies": [],
            "files": {
                "create": [],
                "modify": ["mahabharatha/constants.py"],
                "read": ["mahabharatha/constants.py"],
            },
            "verification": {
                "command": "python -c 'from mahabharatha.constants import PluginHookEvent'",
                "timeout_seconds": 30,
            },
        },
        # ===== Level 2: Core (5 tasks, parallel, depend on Level 1) =====
        {
            "id": "DF-L2-001",
            "title": "Create E2E conftest",
            "description": "Create tests/e2e/conftest.py with test fixtures.",
            "phase": "core",
            "level": 2,
            "dependencies": ["DF-L1-001", "DF-L1-002"],
            "files": {
                "create": ["tests/e2e/conftest.py"],
                "modify": [],
                "read": ["tests/e2e/mock_worker.py", "tests/e2e/harness.py"],
            },
            "verification": {
                "command": "pytest tests/e2e/conftest.py --collect-only",
                "timeout_seconds": 30,
            },
        },
        {
            "id": "DF-L2-002",
            "title": "Create full pipeline test",
            "description": "Create tests/e2e/test_full_pipeline.py for E2EHarness tests.",
            "phase": "core",
            "level": 2,
            "dependencies": ["DF-L2-001"],
            "files": {
                "create": ["tests/e2e/test_full_pipeline.py"],
                "modify": [],
                "read": ["tests/e2e/conftest.py", "tests/e2e/harness.py"],
            },
            "verification": {
                "command": "pytest tests/e2e/test_full_pipeline.py -v --co",
                "timeout_seconds": 30,
            },
        },
        {
            "id": "DF-L2-003",
            "title": "Create plugin unit tests",
            "description": "Create tests/unit/test_plugins.py with tests for plugin ABCs and PluginRegistry.",
            "phase": "core",
            "level": 2,
            "dependencies": ["DF-L1-003", "DF-L1-005"],
            "files": {
                "create": ["tests/unit/test_plugins.py"],
                "modify": [],
                "read": ["mahabharatha/plugins.py", "mahabharatha/constants.py"],
            },
            "verification": {
                "command": "pytest tests/unit/test_plugins.py -v",
                "timeout_seconds": 30,
            },
        },
        {
            "id": "DF-L2-004",
            "title": "Create config unit tests",
            "description": "Create tests/unit/test_plugin_config.py with tests for plugin config Pydantic models.",
            "phase": "core",
            "level": 2,
            "dependencies": ["DF-L1-004"],
            "files": {
                "create": ["tests/unit/test_plugin_config.py"],
                "modify": [],
                "read": ["mahabharatha/plugin_config.py"],
            },
            "verification": {
                "command": "pytest tests/unit/test_plugin_config.py -v",
                "timeout_seconds": 30,
            },
        },
        {
            "id": "DF-L2-005",
            "title": "Integrate plugins into MahabharathaConfig",
            "description": "Add plugins field to MahabharathaConfig in mahabharatha/config.py (optional PluginsConfig).",
            "phase": "core",
            "level": 2,
            "dependencies": ["DF-L1-004"],
            "files": {
                "create": [],
                "modify": ["mahabharatha/config.py"],
                "read": ["mahabharatha/config.py", "mahabharatha/plugin_config.py"],
            },
            "verification": {
                "command": "python -c 'from mahabharatha.config import MahabharathaConfig; MahabharathaConfig()'",
                "timeout_seconds": 30,
            },
        },
        # ===== Level 3: Integration (5 tasks, parallel, depend on Level 2) =====
        {
            "id": "DF-L3-001",
            "title": "Add orchestrator plugin hooks",
            "description": "Integrate PluginRegistry into mahabharatha/orchestrator.py for lifecycle events.",
            "phase": "integration",
            "level": 3,
            "dependencies": ["DF-L2-003"],
            "files": {
                "create": [],
                "modify": ["mahabharatha/orchestrator.py"],
                "read": ["mahabharatha/orchestrator.py", "mahabharatha/plugins.py"],
            },
            "verification": {
                "command": "python -c 'import mahabharatha.orchestrator'",
                "timeout_seconds": 30,
            },
        },
        {
            "id": "DF-L3-002",
            "title": "Add worker plugin hooks",
            "description": "Integrate PluginRegistry into mahabharatha/worker_protocol.py for task events.",
            "phase": "integration",
            "level": 3,
            "dependencies": ["DF-L2-003"],
            "files": {
                "create": [],
                "modify": ["mahabharatha/worker_protocol.py"],
                "read": ["mahabharatha/worker_protocol.py", "mahabharatha/plugins.py"],
            },
            "verification": {
                "command": "python -c 'import mahabharatha.protocol_state'",
                "timeout_seconds": 30,
            },
        },
        {
            "id": "DF-L3-003",
            "title": "Add gate runner plugin hooks",
            "description": "Integrate PluginRegistry into mahabharatha/gates.py for gate events.",
            "phase": "integration",
            "level": 3,
            "dependencies": ["DF-L2-003"],
            "files": {
                "create": [],
                "modify": ["mahabharatha/gates.py"],
                "read": ["mahabharatha/gates.py", "mahabharatha/plugins.py"],
            },
            "verification": {
                "command": "python -c 'import mahabharatha.gates'",
                "timeout_seconds": 30,
            },
        },
        {
            "id": "DF-L3-004",
            "title": "Add launcher plugin support",
            "description": "Integrate LauncherPlugin into mahabharatha/launcher.py.",
            "phase": "integration",
            "level": 3,
            "dependencies": ["DF-L2-003"],
            "files": {
                "create": [],
                "modify": ["mahabharatha/launcher.py"],
                "read": ["mahabharatha/launcher.py", "mahabharatha/plugins.py"],
            },
            "verification": {
                "command": "python -c 'import mahabharatha.launchers'",
                "timeout_seconds": 30,
            },
        },
        {
            "id": "DF-L3-005",
            "title": "Create real execution test",
            "description": "Create tests/e2e/test_real_execution.py with @pytest.mark.real_e2e.",
            "phase": "integration",
            "level": 3,
            "dependencies": ["DF-L2-002"],
            "files": {
                "create": ["tests/e2e/test_real_execution.py"],
                "modify": [],
                "read": ["tests/e2e/harness.py"],
            },
            "verification": {
                "command": "pytest tests/e2e/test_real_execution.py -v --co -m real_e2e",
                "timeout_seconds": 30,
            },
        },
        # ===== Level 4: Testing (5 tasks, parallel, depend on Level 3) =====
        {
            "id": "DF-L4-001",
            "title": "Create plugin lifecycle test",
            "description": "Create tests/integration/test_plugin_lifecycle.py with tests for full plugin event flow.",
            "phase": "testing",
            "level": 4,
            "dependencies": ["DF-L3-001", "DF-L3-002"],
            "files": {
                "create": ["tests/integration/test_plugin_lifecycle.py"],
                "modify": [],
                "read": ["mahabharatha/orchestrator.py", "mahabharatha/worker_protocol.py", "mahabharatha/plugins.py"],
            },
            "verification": {
                "command": "pytest tests/integration/test_plugin_lifecycle.py -v",
                "timeout_seconds": 30,
            },
        },
        {
            "id": "DF-L4-002",
            "title": "Create dogfood E2E test",
            "description": "Create tests/e2e/test_dogfood_plugin.py for plugin system validation.",
            "phase": "testing",
            "level": 4,
            "dependencies": ["DF-L3-005"],
            "files": {
                "create": ["tests/e2e/test_dogfood_plugin.py"],
                "modify": [],
                "read": ["tests/e2e/harness.py", "tests/e2e/conftest.py"],
            },
            "verification": {
                "command": "pytest tests/e2e/test_dogfood_plugin.py -v --co",
                "timeout_seconds": 30,
            },
        },
        {
            "id": "DF-L4-003",
            "title": "Add pytest markers",
            "description": "Add real_e2e marker to pyproject.toml for real Claude API tests.",
            "phase": "testing",
            "level": 4,
            "dependencies": ["DF-L3-005"],
            "files": {
                "create": [],
                "modify": ["pyproject.toml"],
                "read": ["pyproject.toml"],
            },
            "verification": {
                "command": 'python -c \'import tomllib; tomllib.load(open("pyproject.toml","rb"))\'',
                "timeout_seconds": 30,
            },
        },
        {
            "id": "DF-L4-004",
            "title": "Create plugin documentation",
            "description": "Create mahabharatha/data/commands/plugins.md for plugin documentation.",
            "phase": "testing",
            "level": 4,
            "dependencies": ["DF-L3-003", "DF-L3-004"],
            "files": {
                "create": ["mahabharatha/data/commands/plugins.md"],
                "modify": [],
                "read": ["mahabharatha/plugins.py", "mahabharatha/plugin_config.py"],
            },
            "verification": {
                "command": "test -f mahabharatha/data/commands/plugins.md",
                "timeout_seconds": 10,
            },
        },
        {
            "id": "DF-L4-005",
            "title": "Create bug tracking doc",
            "description": "Create claudedocs/dogfood-bugs.md for tracking bugs discovered during dogfooding.",
            "phase": "testing",
            "level": 4,
            "dependencies": [],
            "files": {
                "create": ["claudedocs/dogfood-bugs.md"],
                "modify": [],
                "read": [],
            },
            "verification": {
                "command": "test -f claudedocs/dogfood-bugs.md",
                "timeout_seconds": 10,
            },
        },
    ]


class TestDogfoodPlugin:
    """Test MAHABHARATHA's ability to build its own plugin system via orchestration."""

    def test_plugin_system_builds_via_mahabharatha(self, e2e_harness: E2EHarness) -> None:
        """Construct the 20-task plugin system graph and run full pipeline in mock mode.

        Validates that MAHABHARATHA can orchestrate the plugin system build:
        - All 20 tasks complete successfully
        - All 4 levels merge cleanly
        - All plugin files would be created
        - Full pipeline executes without errors

        This test uses mock mode (no Claude API key required) with 5 workers.
        """
        # Build the 20-task plugin system task graph from design.md
        tasks = _plugin_task_graph()

        # Setup task graph and run with 5 workers
        e2e_harness.setup_task_graph(tasks)
        result = e2e_harness.run(workers=5)

        # Verify all tasks completed successfully
        assert result.success is True, f"Expected success, got {result.tasks_failed} failed tasks"
        assert result.tasks_completed == 20, f"Expected 20 completed, got {result.tasks_completed}"
        assert result.tasks_failed == 0, f"Expected 0 failed, got {result.tasks_failed}"

        # Verify all 4 levels completed
        assert result.levels_completed == 4, f"Expected 4 levels, got {result.levels_completed}"

        # Verify merge commits for all levels
        assert len(result.merge_commits) == 4, f"Expected 4 merge commits, got {len(result.merge_commits)}"

        # Verify reasonable execution time (mock mode should be fast)
        assert result.duration_s < 10.0, f"Expected <10s, took {result.duration_s}s"

    def test_all_plugin_files_created(self, e2e_harness: E2EHarness) -> None:
        """Mock workers create the core plugin module files in the repo."""
        e2e_harness.setup_task_graph(_plugin_task_graph())
        e2e_harness.run(workers=5)

        repo = e2e_harness.repo_path
        # Verify Level 1 foundation files
        assert (repo / "mahabharatha/plugins.py").exists()
        assert (repo / "mahabharatha/plugin_config.py").exists()
        # Verify Level 2 test files
        assert (repo / "tests/unit/test_plugins.py").exists()
        assert (repo / "tests/unit/test_plugin_config.py").exists()
        # Verify Level 3 integration files
        assert (repo / "tests/e2e/test_real_execution.py").exists()

    def test_all_levels_merge(self, e2e_harness: E2EHarness) -> None:
        """Each of the 4 levels produces a merge commit record."""
        e2e_harness.setup_task_graph(_plugin_task_graph())
        result = e2e_harness.run(workers=5)

        assert len(result.merge_commits) == 4
        assert result.levels_completed == 4
