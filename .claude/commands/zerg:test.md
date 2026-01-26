# ZERG Test

Execute tests with coverage analysis and test generation.

## Usage

```bash
/zerg:test [--generate]      # Generate test stubs
           [--coverage]      # Report coverage
           [--watch]         # Watch mode
           [--parallel N]    # Parallel execution
           [--framework pytest|jest|cargo|go]
```

## Capabilities

### Framework Detection
Automatically detects: pytest, jest, cargo test, go test, mocha, vitest

### Test Execution
- Parallel execution for faster runs
- Watch mode for continuous testing
- Coverage tracking per file/function

### Test Generation
Generate test stubs for uncovered code.

## Examples

```bash
# Run all tests
/zerg:test

# Run with coverage
/zerg:test --coverage

# Watch mode
/zerg:test --watch

# Parallel with 8 workers
/zerg:test --parallel 8

# Generate stubs for uncovered code
/zerg:test --generate
```

## Output

```
Test Results
========================================
Total: 285
Passed: 285
Failed: 0
Skipped: 0

Pass Rate: 100.0%
Duration: 4.88s
```

## Exit Codes

- 0: All tests passed
- 1: Some tests failed
- 2: Configuration error
