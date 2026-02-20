# MAHABHARATHA Test Suite

Comprehensive test coverage for the MAHABHARATHA parallel execution system.

## Test Organization

```
tests/
├── unit/                    # Unit tests (isolated, mocked)
│   ├── test_assign.py      # Worker assignment logic
│   ├── test_command_executor.py  # Command execution
│   ├── test_containers.py  # Container management
│   ├── test_context_tracker.py  # Context tracking
│   ├── test_launcher_extended.py  # Launcher edge cases
│   ├── test_levels_extended.py  # Level controller edge cases
│   ├── test_orchestrator_levels.py  # Orchestrator level management
│   ├── test_orchestrator_workers.py  # Worker coordination
│   ├── test_parser.py      # Task graph parsing
│   ├── test_ports_extended.py  # Port allocation edge cases
│   ├── test_security.py    # Security validators
│   ├── test_security_rules.py  # Security rule detection
│   ├── test_state_extended.py  # State manager tracking
│   ├── test_verify.py      # Verification runner
│   └── test_worktree_extended.py  # Worktree edge cases
├── integration/             # Integration tests (component interaction)
│   ├── test_container_lifecycle.py  # Container spawn/stop
│   ├── test_git_ops_extended.py  # Git operations
│   ├── test_merge_coordination.py  # Level merge flow
│   └── test_worker_protocol_extended.py  # Worker protocol
├── e2e/                     # End-to-end tests (full workflows)
│   ├── test_container_e2e.py  # Container mode workflow
│   ├── test_failure_recovery.py  # Failure recovery scenarios
│   ├── test_multilevel_execution.py  # Multi-level task execution
│   └── test_subprocess_e2e.py  # Subprocess mode workflow
└── test_*.py               # Legacy/core tests
```

## Running Tests

### Full Suite
```bash
pytest
```

### With Coverage
```bash
pytest --cov=mahabharatha --cov-report=term-missing
pytest --cov=mahabharatha --cov-report=html  # HTML report in htmlcov/
```

### Specific Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/

# Single module
pytest tests/unit/test_parser.py -v
```

### Parallel Execution
```bash
pytest -n auto  # Use all CPU cores
pytest -n 4     # Use 4 processes
```

## Coverage Targets

| Module | Target | Current |
|--------|--------|---------|
| levels.py | 95%+ | 100% |
| constants.py | 100% | 100% |
| context_tracker.py | 95%+ | 100% |
| parser.py | 95%+ | 98% |
| ports.py | 90%+ | 98% |
| merge.py | 90%+ | 97% |
| verify.py | 90%+ | 96% |
| security.py | 90%+ | 93% |
| assign.py | 85%+ | 91% |
| state.py | 85%+ | 91% |
| orchestrator.py | 75%+ | 76% |
| launcher.py | 70%+ | 75% |

## Writing Tests

### Unit Tests
- Isolate component under test
- Mock all external dependencies
- Test edge cases and error conditions
- Use pytest fixtures for common setup

```python
def test_example_isolated(self) -> None:
    """Test description."""
    with patch("mahabharatha.module.dependency") as mock_dep:
        mock_dep.return_value = expected_value

        result = component_under_test()

        assert result == expected
        mock_dep.assert_called_once()
```

### Integration Tests
- Test component interactions
- Use temporary directories/files
- Mock external services (Docker, git remote)

```python
@pytest.fixture
def integration_setup(tmp_path: Path):
    """Set up integration test environment."""
    # Create necessary structure
    yield tmp_path
    # Cleanup handled by pytest
```

### E2E Tests
- Test complete workflows
- Mock orchestrator dependencies
- Verify state transitions

## Common Fixtures

### `tmp_path`
Pytest built-in for temporary directories.

### `mock_orchestrator_deps`
Comprehensive mock for Orchestrator dependencies:
- StateManager
- LevelController
- TaskParser
- WorktreeManager
- PortAllocator
- SubprocessLauncher
- MergeCoordinator

### `sample_tasks`
Standard task definitions for testing level logic.

## Test Markers

```bash
# Run slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

## Debugging Failed Tests

```bash
# Verbose output
pytest -v --tb=long

# Stop on first failure
pytest -x

# Drop into debugger
pytest --pdb

# Show print statements
pytest -s
```
