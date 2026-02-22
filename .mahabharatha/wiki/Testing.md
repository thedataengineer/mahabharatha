# Testing

This page covers the MAHABHARATHA testing approach: how tests are organized, how to run them, coverage targets, and how to write tests for new features.

---

## Table of Contents

- [Test Organization](#test-organization)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Writing Tests](#writing-tests)
- [Fixtures and Helpers](#fixtures-and-helpers)
- [Coverage Targets](#coverage-targets)
- [Debugging Failed Tests](#debugging-failed-tests)
- [Using /mahabharatha:test](#using-zergtest)

---

## Test Organization

Tests are located in the `tests/` directory and organized by scope:

```
tests/
├── conftest.py                 # Root fixtures (tmp_repo, sample tasks, etc.)
├── unit/                       # Isolated tests with mocked dependencies
│   ├── conftest.py
│   ├── test_assign.py
│   ├── test_containers.py
│   ├── test_launcher.py
│   ├── test_orchestrator_levels.py
│   ├── test_orchestrator_workers.py
│   ├── test_parser.py
│   ├── test_security.py
│   ├── test_state_extended.py
│   ├── test_verify.py
│   └── ...
├── integration/                # Tests verifying component interaction
│   ├── conftest_container.py
│   ├── test_container_lifecycle.py
│   ├── test_git_ops_extended.py
│   ├── test_merge_coordination.py
│   ├── test_rush_flow.py
│   └── ...
├── e2e/                        # Full workflow tests
│   ├── conftest.py
│   ├── harness.py              # E2E test harness utilities
│   ├── mock_worker.py          # Mock worker for E2E tests
│   ├── test_full_pipeline.py
│   ├── test_failure_recovery.py
│   ├── test_multilevel_execution.py
│   └── ...
├── fixtures/                   # Shared test data files
├── helpers/                    # Reusable test utility functions
├── mocks/                      # Shared mock objects
└── test_*.py                   # Root-level tests (core modules)
```

Root-level `test_*.py` files cover core modules directly. New tests should go in the appropriate subdirectory (`unit/`, `integration/`, or `e2e/`).

---

## Running Tests

### Full Test Suite

```bash
pytest
```

### With Coverage Report

```bash
# Terminal output with missing line numbers
pytest --cov=mahabharatha --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov=mahabharatha --cov-report=html
# Open htmlcov/index.html
```

### By Category

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# End-to-end tests only
pytest tests/e2e/

# Root-level tests
pytest tests/test_*.py
```

### Single File or Test

```bash
# One file, verbose
pytest tests/unit/test_launcher.py -v

# One specific test
pytest tests/unit/test_launcher.py::TestLauncher::test_spawn_worker -v
```

### Parallel Execution

```bash
# Auto-detect CPU cores
pytest -n auto

# Specify process count
pytest -n 4
```

### Test Markers

```bash
# Run only slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

---

## Test Categories

### Unit Tests

**Location:** `tests/unit/`

**Purpose:** Test individual components in isolation. All external dependencies are mocked.

**Characteristics:**
- Fast execution (milliseconds per test).
- No filesystem, network, or Docker dependencies.
- Each test verifies a single behavior.
- Mocks are used for all collaborators.

**Example:**

```python
from unittest.mock import patch, MagicMock

def test_level_controller_advances_when_all_complete():
    """Level controller advances to next level when all tasks complete."""
    with patch("mahabharatha.levels.StateManager") as mock_state:
        mock_state.get_level_tasks.return_value = [
            {"id": "t1", "status": "completed"},
            {"id": "t2", "status": "completed"},
        ]

        controller = LevelController(mock_state)
        result = controller.should_advance(level=1)

        assert result is True
```

### Integration Tests

**Location:** `tests/integration/`

**Purpose:** Test how multiple components work together. External services (Docker, git remotes) are mocked, but internal component interactions are real.

**Characteristics:**
- Moderate execution time.
- Use temporary directories and files.
- Test realistic component interaction paths.
- Mock external services but not internal dependencies.

**Example:**

```python
@pytest.fixture
def integration_setup(tmp_path: Path):
    """Set up integration test environment."""
    config = MahabharathaConfig(workers=2, timeout=30)
    state = StateManager(tmp_path / "state.json")
    yield tmp_path, config, state

def test_merge_after_level_completion(integration_setup):
    """Merge coordinator merges branches after all tasks complete."""
    tmp_path, config, state = integration_setup
    # Set up completed tasks, verify merge triggers
    ...
```

### End-to-End Tests

**Location:** `tests/e2e/`

**Purpose:** Test complete workflows from start to finish, simulating the full MAHABHARATHA pipeline.

**Characteristics:**
- Longer execution time.
- Use the E2E harness (`harness.py`) and mock worker (`mock_worker.py`).
- Verify state transitions across the full lifecycle.
- Test failure recovery and multi-level execution.

**Example:**

```python
def test_full_pipeline_two_levels(tmp_repo):
    """Full pipeline: plan -> design -> kurukshetra -> merge across 2 levels."""
    harness = E2EHarness(tmp_repo)
    harness.setup_feature("test-feature")
    harness.run_rush(workers=2)

    assert harness.all_tasks_completed()
    assert harness.final_merge_succeeded()
```

---

## Writing Tests

### Where to Put New Tests

| What you changed | Where to add tests |
|------------------|--------------------|
| Single function or class | `tests/unit/test_<module>.py` |
| Interaction between modules | `tests/integration/test_<feature>.py` |
| New command or workflow | `tests/e2e/test_<workflow>.py` |
| Bug fix | Add a regression test in the most specific category |

### Test Naming

Name tests to describe the behavior being verified:

```python
# Good: describes the scenario and expected outcome
def test_worker_retries_on_transient_failure():
def test_port_allocator_raises_on_exhaustion():
def test_state_manager_recovers_from_corrupt_json():

# Bad: vague or implementation-focused
def test_worker():
def test_ports():
def test_state_json():
```

### Test Structure

Follow the Arrange-Act-Assert pattern:

```python
def test_task_parser_extracts_dependencies():
    """Parser correctly extracts task dependencies from graph JSON."""
    # Arrange
    graph_json = {
        "tasks": [
            {"id": "t1", "dependencies": []},
            {"id": "t2", "dependencies": ["t1"]},
        ]
    }

    # Act
    parser = TaskParser()
    result = parser.parse(graph_json)

    # Assert
    assert result["t2"].dependencies == ["t1"]
    assert result["t1"].dependencies == []
```

### Mocking Guidelines

- Mock at the boundary of the component under test, not deeper.
- Use `unittest.mock.patch` for replacing dependencies.
- Prefer `MagicMock` for objects with many methods.
- Use `tmp_path` (pytest built-in) for filesystem operations.

```python
# Good: mock the external boundary
with patch("mahabharatha.launcher.subprocess.run") as mock_run:
    mock_run.return_value = CompletedProcess(args=[], returncode=0)
    launcher.spawn_worker(task)
    mock_run.assert_called_once()

# Bad: mock deep internals
with patch("mahabharatha.launcher.SubprocessLauncher._internal_method"):
    ...
```

### Testing Error Conditions

Always test error paths, not just happy paths:

```python
def test_state_manager_raises_on_missing_file():
    """StateManager raises FileNotFoundError for missing state file."""
    manager = StateManager(Path("/nonexistent/state.json"))

    with pytest.raises(FileNotFoundError):
        manager.load()

def test_launcher_handles_docker_timeout():
    """Launcher raises TimeoutError when Docker container does not start."""
    with patch("mahabharatha.launcher.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker", timeout=30)

        with pytest.raises(TimeoutError):
            launcher.spawn_container(task)
```

---

## Fixtures and Helpers

### Root Fixtures (tests/conftest.py)

| Fixture | Description |
|---------|-------------|
| `tmp_repo` | Creates a temporary git repository with initial commit. Changes directory to it and restores on cleanup. |
| `sample_tasks` | Standard task definitions for testing level logic. |
| `mock_orchestrator_deps` | Comprehensive mock covering StateManager, LevelController, TaskParser, WorktreeManager, PortAllocator, SubprocessLauncher, MergeCoordinator. |

### E2E Helpers (tests/e2e/)

| Helper | Description |
|--------|-------------|
| `harness.py` | E2E test harness for setting up features, running kurukshetra, and asserting outcomes. |
| `mock_worker.py` | Simulated worker that creates files and reports task completion without calling the Claude API. |

### Creating New Fixtures

If a fixture is used across multiple test files, place it in the appropriate `conftest.py`:

- `tests/conftest.py` -- Shared across all test categories.
- `tests/unit/conftest.py` -- Shared across unit tests.
- `tests/integration/conftest.py` -- Shared across integration tests.
- `tests/e2e/conftest.py` -- Shared across E2E tests.

---

## Coverage Targets

Current coverage targets by module:

| Module | Target | Notes |
|--------|--------|-------|
| `levels.py` | 95%+ | Core coordination logic |
| `constants.py` | 100% | Simple constants |
| `context_tracker.py` | 95%+ | Token tracking |
| `parser.py` | 95%+ | Task graph parsing |
| `ports.py` | 90%+ | Port allocation |
| `merge.py` | 90%+ | Branch merging |
| `verify.py` | 90%+ | Verification runner |
| `security.py` | 90%+ | Security validation |
| `assign.py` | 85%+ | Worker assignment |
| `state.py` | 85%+ | State management |
| `orchestrator.py` | 75%+ | Complex coordination |
| `launcher.py` | 70%+ | Process/container spawning |

When adding new code, aim for at least 85% coverage on the new lines. Use the coverage report to identify untested paths:

```bash
pytest --cov=mahabharatha --cov-report=term-missing tests/unit/test_<your_module>.py
```

---

## Debugging Failed Tests

### Verbose Output

```bash
pytest -v --tb=long
```

### Stop on First Failure

```bash
pytest -x
```

### Drop into Debugger on Failure

```bash
pytest --pdb
```

### Show Print Statements

```bash
pytest -s
```

### Run a Single Failing Test

```bash
pytest tests/unit/test_launcher.py::TestLauncher::test_spawn_worker -v --tb=long
```

### Common Causes of Test Failures

| Symptom | Likely Cause |
|---------|-------------|
| `FileNotFoundError` in tests | Test is not using `tmp_path` or `tmp_repo` fixture |
| Tests pass individually but fail together | Shared mutable state between tests |
| Tests fail in CI but pass locally | Missing fixture, environment dependency, or timing issue |
| `ModuleNotFoundError` | Package not installed in dev mode (`pip install -e ".[dev]"`) |

---

## Using /mahabharatha:test

The `/mahabharatha:test` slash command provides a convenient interface for running tests within a Claude Code session.

### Basic Usage

```
/mahabharatha:test                      # Run all tests
/mahabharatha:test --coverage           # Run with coverage report
/mahabharatha:test --parallel 8         # Run with 8 parallel workers
/mahabharatha:test --watch              # Watch mode for continuous testing
/mahabharatha:test --generate           # Generate test stubs for uncovered code
```

### Framework Detection

`/mahabharatha:test` automatically detects the test framework. For MAHABHARATHA, it detects pytest.

### Test Generation

The `--generate` flag creates test stubs for code that lacks test coverage:

```
/mahabharatha:test --generate
```

This scans the codebase, identifies uncovered functions and classes, and creates skeleton test files. You must fill in the actual test logic.

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All tests passed |
| 1 | Some tests failed |
| 2 | Configuration error |

---

## See Also

- [[Contributing]] -- Development setup and PR process
- [[Debug Guide]] -- Diagnosing issues during development
- [[Troubleshooting]] -- Common runtime issues and solutions
