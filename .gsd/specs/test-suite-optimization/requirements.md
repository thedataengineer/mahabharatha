# Requirements: test-suite-optimization

**Status: APPROVED**
**Created**: 2026-02-04
**Feature**: Test Suite Optimization

## Problem Statement

The MAHABHARATHA test suite has grown to 7,634 tests (128K LOC) for 55K LOC of production code — a 2.3:1 ratio that significantly exceeds industry norms (1:1 to 1.5:1). This causes:

1. **CI time**: 8-10 minutes per run, target is < 2 minutes
2. **Local dev feedback**: Too slow for rapid iteration
3. **Mahabharatha kurukshetra bottleneck**: Gates take too long, slowing parallel worker coordination

### Root Causes Identified

- **No test tiering**: All 7,634 tests run on every change
- **Zero parameterization**: Major test files have repetitive individual tests (31 identical pattern tests in test_debug_cmd.py)
- **Excessive fragmentation**: 12 launcher test files (8,145 LOC) for a single module
- **Long gate timeouts**: 600s for test gate
- **No smoke test tier**: No fast feedback path

## Functional Requirements

### FR-1: Test Tiering System

Implement three-tier test execution:

| Tier | Purpose | Test Count | Target Time | Trigger |
|------|---------|------------|-------------|---------|
| Smoke | Critical path validation | ~200 | < 30s | Every push |
| Fast | Core unit tests | ~2000 | < 90s | PR open/sync |
| Full | Complete suite | All | < 10 min | Pre-merge, nightly |

**Acceptance Criteria**:
- [ ] `pytest -m smoke` runs in < 30 seconds
- [ ] Smoke tests cover: config, state, types, validation, constants
- [ ] Fast tests exclude slow-marked tests
- [ ] CI runs smoke tier before other jobs

### FR-2: Test Parameterization

Refactor repetitive tests using `@pytest.mark.parametrize`:

| Target File | Current | After | LOC Saved |
|-------------|---------|-------|-----------|
| test_debug_cmd.py | 139 tests | 50 | ~1,100 |
| test_security_rules_full.py | 121 tests | 40 | ~600 |
| test_launcher.py | 124 tests | 60 | ~400 |

**Acceptance Criteria**:
- [ ] TestStackTraceAnalyzer reduced from 31 to 1 parameterized test
- [ ] Language detection tests consolidated
- [ ] Test coverage unchanged (same assertions, different structure)

### FR-3: Test File Consolidation

Consolidate launcher test files from 12 to 4:

**Target structure**:
```
tests/unit/test_launcher.py           # Core subprocess
tests/unit/test_launcher_container.py # Container-specific
tests/integration/test_launcher_integration.py
tests/e2e/test_launcher_e2e.py
```

**Files to merge/delete**:
- test_launcher_coverage.py → test_launcher.py
- test_launcher_errors.py → test_launcher.py
- test_launcher_extended.py → test_launcher.py
- test_launcher_process.py → test_launcher_container.py
- test_launcher_network.py → test_launcher_container.py
- test_launcher_exec.py → test_launcher_container.py

**Acceptance Criteria**:
- [ ] 12 files reduced to 4
- [ ] No test coverage loss
- [ ] All tests still pass

### FR-4: Gate Configuration Optimization

Update `.mahabharatha/config.yaml` quality gates:

```yaml
quality_gates:
  - name: smoke
    command: pytest -m smoke -x --timeout=5 -q
    required: true
    timeout: 60
  - name: test
    command: pytest tests/unit -m "not slow" -x --timeout=15 -q
    required: true
    timeout: 180
```

**Acceptance Criteria**:
- [ ] Smoke gate added (60s timeout)
- [ ] Test gate timeout reduced to 180s (was 600s)
- [ ] Coverage gate moved to nightly-only

### FR-5: CI Pipeline Optimization

Update `.github/workflows/pytest.yml`:

- Add smoke job that gates other jobs
- Add parallel sharding for unit tests (4 runners)
- Add pip caching
- Add pytest-xdist for local parallel runs

**Acceptance Criteria**:
- [ ] Smoke job runs first, other jobs depend on it
- [ ] Unit tests sharded across 4 parallel runners
- [ ] Total CI time < 2 minutes

## Non-Functional Requirements

### NFR-1: Quality Preservation
- Coverage threshold: **80%** (unchanged)
- All existing test assertions must be preserved
- No reduction in defect detection capability

### NFR-2: Security
- Security gate (ruff --select S) remains active
- No security-related tests can be removed or weakened

### NFR-3: Performance
- Smoke tests: < 30 seconds
- Fast tests: < 90 seconds
- Full tests: < 10 minutes
- Local dev: `pytest -n auto` parallelizes automatically

### NFR-4: Maintainability
- Parameterized tests easier to extend (add case, not function)
- Consolidated files reduce cognitive load
- Clear tier markers for test classification

## Scope Boundaries

### In Scope
- Test tiering via pytest markers
- Parameterization of repetitive tests
- Launcher test file consolidation
- Gate configuration updates
- CI workflow optimization

### Out of Scope
- E2E tests (require real Claude API, stay nightly-only)
- Docker tests (stay marker-gated)
- Smart test selection based on changed files (Phase 3, future)
- Shared fixtures library (Phase 3, future)

## Dependencies

### New Dependencies
- `pytest-xdist>=3.0` — Parallel local test execution
- `pytest-split>=0.8` — CI test sharding

### Existing Dependencies (unchanged)
- `pytest>=7.0`
- `pytest-cov>=4.0`
- `pytest-asyncio>=0.21`
- `pytest-timeout>=2.0`

## Implementation Phases

### Phase 1: Quick Wins (1-2 hours)
1. Add smoke markers to 5 critical test files
2. Update pyproject.toml with new markers
3. Update .mahabharatha/config.yaml gates
4. Add pytest-xdist dependency
5. Update CI workflow with smoke job

**Expected impact**: 40% CI time reduction

### Phase 2: Parameterization + Consolidation (1 day)
1. Parameterize test_debug_cmd.py (31→1 test)
2. Parameterize test_security_rules_full.py
3. Consolidate launcher test files (12→4)
4. Add CI parallel sharding

**Expected impact**: Additional 30% reduction

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| PR CI time | 8-10 min | < 2 min |
| Smoke feedback | N/A | < 30s |
| Test count | 7,634 | ~5,500 |
| Test LOC | 128K | ~100K |
| Gate timeout | 600s | 180s |
| Launcher test files | 12 | 4 |

## Open Questions

None — all questions resolved through Socratic dialogue.

## Approval

- [ ] Requirements reviewed and approved
- [ ] Ready for /mahabharatha:design phase
