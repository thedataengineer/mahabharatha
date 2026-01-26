# ZERG Refactor

Automated code improvement and cleanup.

## Usage

```bash
/zerg:refactor [--transforms dead-code,simplify,types,patterns,naming]
               [--dry-run]
               [--interactive]
```

## Transforms

### dead-code
Remove unused imports, variables, and functions.

### simplify
Simplify complex expressions:
- `if x == True:` → `if x:`
- `if x == None:` → `if x is None:`
- Redundant parentheses
- Unnecessary else after return

### types
Strengthen type annotations:
- Add missing type hints
- Replace `Any` with specific types
- Add return type annotations

### patterns
Apply common design patterns:
- Extract repeated code
- Apply guard clauses
- Use early returns

### naming
Improve variable and function names:
- Replace single-letter names
- Fix casing conventions
- Make names more descriptive

## Examples

```bash
# Run all transforms (dry-run)
/zerg:refactor --transforms dead-code,simplify --dry-run

# Interactive mode
/zerg:refactor --interactive

# Specific transforms
/zerg:refactor --transforms types,naming
```

## Output

```
Refactor Results
========================================
Files Analyzed: 15
Suggestions: 23
Applied: 0

Suggestions:
  simplify:
    auth.py:42
      - if authenticated == True:
      + if authenticated:
```

## Exit Codes

- 0: No issues (or all applied)
- 1: Suggestions available
- 2: Error during analysis
