# Technical Design: mahabharatha-estimate

## Metadata
- **Feature**: mahabharatha-estimate
- **Status**: DRAFT
- **Created**: 2026-01-31

---

## 1. Overview

### 1.1 Summary
Create `/mahabharatha:estimate` — a split command (core + details) providing full-lifecycle effort estimation: pre-execution PERT with risk weighting, post-execution comparison, historical calibration, and API cost projection. No new Python modules — leverages existing `risk_scoring.py`, `whatif.py`, `metrics.py`, and `.mahabharatha/estimate.py` via `python -c` inline execution.

### 1.2 Goals
- Pre-execution: PERT estimates with confidence intervals (P50/P80/P95) per task, level, feature
- Post-execution: compare estimates vs actuals, flag outliers
- Calibration: compute historical bias, auto-apply to future estimates
- Cost: project API token usage and cost per worker count

### 1.3 Non-Goals
- New Python module or CLI entry point
- Real-time tracking during execution (use `/mahabharatha:status`)
- Worker assignment optimization (use `WhatIfEngine` directly)

---

## 2. Architecture

### 2.1 Data Flow

```
task-graph.json ──┐
                  ├──▶ Pre-Estimate ──▶ .gsd/estimates/{feature}-estimate.json
risk_scoring.py ──┘         │
                            ▼
                     Output (text/json/md)

.mahabharatha/state/*.json ──┐
                     ├──▶ Post-Compare ──▶ append to history JSON
metrics.py ──────────┘         │
pre-estimate.json ─────────────┘
                            ▼
                     Comparison tables

.gsd/estimates/*.json ──▶ Calibrate ──▶ .gsd/estimates/calibration.json
                              │
                              ▼
                     Bias factors + recommendations
```

### 2.2 Component Breakdown

| Component | Responsibility | Files |
|-----------|---------------|-------|
| Core command | Flags, auto-detect, workflow orchestration, task tracking | `mahabharatha:estimate.core.md` |
| Details reference | PERT math, output templates, calibration algo, JSON schemas | `mahabharatha:estimate.details.md` |
| Parent file | Backward compat (= core content) | `mahabharatha:estimate.md` |
| History store | Per-feature pre/post snapshots | `.gsd/estimates/{feature}-estimate.json` |
| Calibration store | Aggregated bias factors | `.gsd/estimates/calibration.json` |

---

## 3. Key Decisions

### Decision: Command-file only (no new Python)

**Context**: Could create a new `mahabharatha/estimate_cmd.py` module, but existing classes already provide all computation.

**Decision**: Pure markdown command files that instruct Claude to run `python -c` with existing modules.

**Rationale**: Minimizes code surface, leverages tested code, follows pattern of other simple commands (analyze, review, test).

### Decision: PERT + risk weighting over simple multipliers

**Context**: `.mahabharatha/estimate.py` uses fixed multipliers (1.0x/1.7x/2.7x). PERT with risk weighting produces more nuanced estimates.

**Decision**: PERT formula `(O+4M+P)/6` with risk-derived O/P bounds.

**Rationale**: Risk grade A tasks get tight bounds (low variance), grade D tasks get wide bounds (high variance). More realistic than flat multipliers.

### Decision: Auto-apply calibration bias

**Context**: Could just display bias as recommendation vs automatically adjusting estimates.

**Decision**: Auto-apply from `.gsd/estimates/calibration.json` when present.

**Rationale**: Reduces cognitive overhead. User can override with `--no-calibration` if needed.

---

## 4. Implementation Plan

### Phase Summary

| Phase | Tasks | Parallel |
|-------|-------|----------|
| Foundation (L1) | 2 | Yes |
| Integration (L2) | 1 | No |
| Verification (L3) | 1 | No |

### File Ownership

| File | Task ID | Operation |
|------|---------|-----------|
| `mahabharatha/data/commands/mahabharatha:estimate.core.md` | TASK-L1-001 | create |
| `mahabharatha/data/commands/mahabharatha:estimate.details.md` | TASK-L1-002 | create |
| `mahabharatha/data/commands/mahabharatha:estimate.md` | TASK-L2-001 | create |
| `claudedocs/backlog.md` | TASK-L2-001 | modify |

---

## 5. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| `python -c` imports fail in worker env | Low | Med | Fallback: describe algorithm in markdown for Claude to compute manually |
| Split files exceed 300 lines | Low | Low | Details file can grow; no hard limit |
| Calibration with < 3 features is noisy | Med | Low | Show warning when < 3 features in calibration |

---

## 6. Testing Strategy

### Verification Commands
- All 3 files exist: `ls mahabharatha/data/commands/mahabharatha:estimate{,.core,.details}.md`
- Task tracking present: `grep -c "TaskCreate\|TaskUpdate" mahabharatha/data/commands/mahabharatha:estimate*.md`
- Split markers: `grep "SPLIT" mahabharatha/data/commands/mahabharatha:estimate.{core,details}.md`
- PERT formula: `grep "PERT\|optimistic\|pessimistic" mahabharatha/data/commands/mahabharatha:estimate.details.md`
- Drift detection: `grep -rL "TaskCreate\|TaskUpdate\|TaskList\|TaskGet" mahabharatha/data/commands/mahabharatha:*.md` returns empty
- Backlog updated: `grep "DONE" claudedocs/backlog.md | grep estimate`
- Existing tests pass: `python -m pytest tests/ -x -q`

---

## 7. Parallel Execution Notes

- L1: 2 tasks (core + details), fully parallel
- L2: 1 task (parent + backlog), depends on both L1 tasks
- L3: 1 task (verification), depends on L2
- Optimal workers: 2
- Max workers: 2
