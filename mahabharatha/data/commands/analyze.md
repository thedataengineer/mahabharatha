# Mahabharatha Analyze

Run static analysis, complexity metrics, and quality assessment.

## Pre-Flight

```bash
# Analyze can run anywhere, no prerequisites
```

## Usage

```bash
/mahabharatha:analyze [--check lint|complexity|coverage|security|all]
              [--format text|json|sarif]
              [--threshold complexity=10,coverage=70]
              [--files path/to/files]
```

## Check Types

### Lint
Language-specific linting (ruff for Python, eslint for JS, etc.)

### Complexity
Cyclomatic and cognitive complexity analysis.

### Coverage
Test coverage analysis and reporting.

### Security
SAST scanning for vulnerabilities (bandit, semgrep).

## Examples

```bash
# Run all checks
/mahabharatha:analyze --check all

# Lint only with JSON output
/mahabharatha:analyze --check lint --format json

# Custom thresholds
/mahabharatha:analyze --check complexity --threshold complexity=15

# SARIF for IDE integration
/mahabharatha:analyze --check all --format sarif > results.sarif
```

## Output Formats

- **text**: Human-readable summary
- **json**: Machine-parseable JSON
- **sarif**: Static Analysis Results Interchange Format (IDE integration)

## Task Tracking

On invocation, create a Claude Code Task to track this command:

Call TaskCreate:
  - subject: "[Analyze] Run {check} analysis"
  - description: "Running {check} analysis. Format: {format}. Thresholds: {thresholds}."
  - activeForm: "Running analysis"

Immediately call TaskUpdate:
  - taskId: (the Claude Task ID)
  - status: "in_progress"

On completion, call TaskUpdate:
  - taskId: (the Claude Task ID)
  - status: "completed"

## Exit Codes

- 0: All checks passed
- 1: One or more checks failed
- 2: Configuration error

## Help

When `--help` is passed in `$ARGUMENTS`, display usage and exit:

```
/mahabharatha:analyze — Run static analysis, complexity metrics, and quality assessment.

Flags:
  --check <lint|complexity|coverage|security|all>
                      Type of analysis to run
  --format <text|json|sarif>
                      Output format
  --threshold <key=value,...>
                      Custom thresholds (e.g., complexity=10,coverage=70)
  --files <path>      Specific files to analyze
  --help              Show this help message
```
