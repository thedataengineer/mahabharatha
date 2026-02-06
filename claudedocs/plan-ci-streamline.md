# Plan: Streamline CI into Single Workflow

## Problem

- 4 separate workflows (changelog-check, command-validation, pytest, release) = 4 check suites, excess runner contention
- Sequential gating adds ~30s overhead: `smoke` (0 tests) → `lint` → tests
- Command validation runs twice (own workflow + inside integration job)
- 8 parallel jobs compete for runners (cause of stuck `test(3)` on PR #153)
- Integration tests unsharded (~2min bottleneck)

## Target Architecture

```
Single workflow: ci.yml
Trigger: push(main), PR

                 ┌─────────────┐
                 │   quality    │  lint + validate + changelog (~20s)
                 └──────┬──────┘
                        │
              ┌─────────┴─────────┐
              │                   │
        ┌─────┴─────┐     ┌──────┴──────┐
        │   tests   │     │    audit    │
        │ unit+integ│     │  pip-audit  │
        │ (2 shards)│     └─────────────┘
        └───────────┘

Total jobs: 4 (quality + 2 test shards + audit)
Previous:   8 (smoke + lint + 4 unit shards + integration + audit + changelog + validate)
```

## Changes

### 1. Merge workflows

- Delete `changelog-check.yml`, `command-validation.yml`
- Rename `pytest.yml` → `ci.yml`
- Keep `release.yml` separate (different trigger: release published)

### 2. Create `quality` job (replaces smoke + lint + changelog + validate)

Single job runs sequentially:
1. `ruff check .` + `ruff format --check .`
2. `python -m zerg.validate_commands`
3. Changelog diff check (inline, skip if `skip-changelog` label present)

Estimated: ~20s total (one runner startup instead of four)

### 3. Consolidate test sharding

- Merge unit + integration into 2 shards using `pytest-split`
- Command: `pytest tests/ -m "not slow" --splits 2 --group N`
- Reduces from 5 test jobs (4 unit + 1 integration) to 2

### 4. Keep audit as-is

- `pip-audit --desc` parallel with tests
- No gating (informational)

### 5. Delete smoke job

- 0 tests use `@pytest.mark.smoke` marker
- Pure overhead (~15s job start + teardown for nothing)

## Expected Results

| Metric | Before | After |
|--------|--------|-------|
| Workflows triggered on PR | 3 | 1 |
| Total jobs | 8 | 4 |
| Runner startups | 8 | 4 |
| Critical path time | ~2.5min | ~1.5min |
| Job start overhead | ~120s (8×15s) | ~60s (4×15s) |

## Files to Modify

- `DELETE .github/workflows/changelog-check.yml`
- `DELETE .github/workflows/command-validation.yml`
- `RENAME .github/workflows/pytest.yml` → `.github/workflows/ci.yml`
- `KEEP .github/workflows/release.yml` (unchanged)

## Unresolved Questions

- Should we keep `pytest-split` or switch to duration-based sharding with `pytest-xdist`?
- Do any branch protection rules reference specific workflow/job names that would break on rename?
- Should `audit` be promoted to blocking (fail CI on known vulnerabilities)?
