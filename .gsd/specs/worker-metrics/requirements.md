# Feature Requirements: worker-metrics

## Metadata
- **Feature**: worker-metrics
- **Status**: DRAFT
- **Created**: 2026-01-27T12:00:00
- **Author**: MAHABHARATHA Plan Mode

---

## 1. Problem Statement

### 1.1 Background
MAHABHARATHA orchestrates parallel Claude Code workers but lacks visibility into worker performance. Current state tracks basic status but not timing, throughput, or efficiency metrics.

### 1.2 Problem
No way to understand:
- How long workers take to initialize
- Per-task execution duration
- Worker efficiency and utilization
- Level completion performance
- Historical metrics for optimization

### 1.3 Impact
Without metrics:
- Can't identify slow workers or tasks
- Can't optimize worker count decisions
- Can't predict completion times
- Can't detect performance regressions

---

## 2. Users

### 2.1 Primary Users
- Developers running MAHABHARATHA kurukshetra to complete features

### 2.2 User Stories
- As a developer, I want to see how long each worker takes so I can identify bottlenecks
- As a developer, I want task-level timing so I can optimize verification commands
- As a developer, I want level metrics so I can understand parallelization efficiency

---

## 3. Functional Requirements

### 3.1 Core Capabilities

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-001 | Track worker initialization duration | Must | ready_at - started_at |
| FR-002 | Track per-task execution duration | Must | completed_at - started_at |
| FR-003 | Track queue wait time | Must | claimed_at - created_at |
| FR-004 | Track verification duration per task | Must | Already in VerificationResult |
| FR-005 | Compute worker uptime | Must | Current time - started_at |
| FR-006 | Compute tasks/worker throughput | Should | tasks_completed / uptime |
| FR-007 | Track context usage over time | Should | Samples array |
| FR-008 | Compute level duration | Must | completed_at - started_at |
| FR-009 | Compute parallelization efficiency | Should | concurrent_tasks / max_workers |
| FR-010 | Persist metrics to state file | Must | Survives restarts |
| FR-011 | Export metrics as JSON | Should | For external analysis |
| FR-012 | Calculate percentiles (p50/p95/p99) | Could | For distribution analysis |

### 3.2 Inputs
- Existing state events (task transitions, worker spawns)
- Timestamps from orchestrator lifecycle
- Claude invocation results (already have duration_ms)

### 3.3 Outputs
- Enhanced `mahabharatha status` display with metrics
- Metrics section in state JSON
- Optional JSON export

---

## 4. Non-Functional Requirements

### 4.1 Performance
- Metrics computation: <100ms overhead
- State file write: <50ms additional
- No impact on worker execution

### 4.2 Reliability
- Metrics persist across crashes/restarts
- Missing timestamps don't crash system

---

## 5. Scope

### 5.1 In Scope
- Worker timing metrics (init, task, uptime)
- Task timing metrics (queue, execution, verification)
- Level timing metrics (duration, efficiency)
- Aggregations (totals, averages, percentiles)
- Persistence in state file
- Enhanced status display
- JSON export capability

### 5.2 Out of Scope
- Prometheus/metrics server (future)
- Historical cross-feature comparison (future)
- Real-time streaming metrics (future)
- Resource utilization (CPU/memory) (future)

---

## 6. Technical Design

### 6.1 New Types (mahabharatha/types.py)

```python
@dataclass
class WorkerMetrics:
    worker_id: int
    initialization_ms: int | None
    uptime_ms: int
    tasks_completed: int
    tasks_failed: int
    total_task_duration_ms: int
    avg_task_duration_ms: float
    context_samples: list[tuple[datetime, float]]

@dataclass
class TaskMetrics:
    task_id: str
    queue_wait_ms: int | None
    execution_duration_ms: int | None
    verification_duration_ms: int | None
    total_duration_ms: int | None

@dataclass
class LevelMetrics:
    level: int
    duration_ms: int | None
    task_count: int
    max_parallel: int
    avg_task_duration_ms: float
    p50_duration_ms: int
    p95_duration_ms: int

@dataclass
class FeatureMetrics:
    total_duration_ms: int | None
    workers_used: int
    tasks_total: int
    tasks_completed: int
    tasks_failed: int
    levels_completed: int
    worker_metrics: list[WorkerMetrics]
    level_metrics: list[LevelMetrics]
```

### 6.2 Extended Fields

**WorkerState** - add:
- `ready_at: datetime | None`
- `last_task_completed_at: datetime | None`

**TaskExecution** - add:
- `claimed_at: str | None`
- `duration_ms: int | None`

### 6.3 New Module (mahabharatha/metrics.py)

```python
class MetricsCollector:
    def __init__(self, state: StateManager)
    def compute_worker_metrics(worker_id: int) -> WorkerMetrics
    def compute_task_metrics(task_id: str) -> TaskMetrics
    def compute_level_metrics(level: int) -> LevelMetrics
    def compute_feature_metrics() -> FeatureMetrics
    def export_json(path: Path) -> None
```

### 6.4 State Schema Extension

```json
{
  "metrics": {
    "computed_at": "ISO timestamp",
    "feature_metrics": { ... },
    "worker_metrics": [ ... ],
    "level_metrics": [ ... ]
  }
}
```

---

## 7. Files to Modify

| File | Changes | Priority |
|------|---------|----------|
| `mahabharatha/types.py` | Add metric types, extend WorkerState/TaskExecution | P0 |
| `mahabharatha/metrics.py` | New MetricsCollector class | P0 |
| `mahabharatha/state.py` | Store/compute metrics, timestamp tracking | P0 |
| `mahabharatha/orchestrator.py` | Record timestamps, trigger metrics computation | P1 |
| `mahabharatha/commands/status.py` | Display metrics in status output | P1 |
| `.mahabharatha/schemas/state.schema.json` | Add metrics schema section | P1 |
| `tests/unit/test_metrics.py` | Unit tests for MetricsCollector | P2 |

---

## 8. Acceptance Criteria

### 8.1 Definition of Done
- [ ] All metric types defined
- [ ] MetricsCollector computes all metrics
- [ ] Metrics persist in state file
- [ ] `mahabharatha status` shows metrics summary
- [ ] Unit tests for metrics calculations
- [ ] Integration test with mock kurukshetra

### 8.2 Test Scenarios

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| TC-001 | Worker init timing | Worker spawns | Ready state reached | initialization_ms calculated |
| TC-002 | Task duration | Task starts/completes | Status check | duration_ms accurate |
| TC-003 | Level metrics | Level completes | Metrics computed | p50/p95 available |
| TC-004 | Status display | Kurukshetra in progress | `mahabharatha status` | Metrics shown |
| TC-005 | Persistence | Metrics computed | State saved | Metrics in JSON |

---

## 9. Task Breakdown (MAHABHARATHA Tasks)

### Level 0: Foundation
| Task | Files | Description |
|------|-------|-------------|
| WM-001 | `mahabharatha/types.py` | Add WorkerMetrics, TaskMetrics, LevelMetrics, FeatureMetrics types |

### Level 1: Core Implementation
| Task | Files | Deps | Description |
|------|-------|------|-------------|
| WM-002 | `mahabharatha/metrics.py` | WM-001 | Create MetricsCollector class with compute methods |
| WM-003 | `mahabharatha/state.py` | WM-001 | Extend state with timestamp tracking and metrics storage |
| WM-004 | `.mahabharatha/schemas/state.schema.json` | WM-001 | Add metrics schema section |

### Level 2: Integration
| Task | Files | Deps | Description |
|------|-------|------|-------------|
| WM-005 | `mahabharatha/orchestrator.py` | WM-002, WM-003 | Record timestamps, trigger metrics computation |
| WM-006 | `mahabharatha/commands/status.py` | WM-002 | Display metrics in status output |

### Level 3: Testing
| Task | Files | Deps | Description |
|------|-------|------|-------------|
| WM-007 | `tests/unit/test_metrics.py` | WM-002 | Unit tests for MetricsCollector |
| WM-008 | `tests/integration/test_metrics_integration.py` | WM-005, WM-006 | Integration tests |

---

## 10. Open Questions

| ID | Question | Status |
|----|----------|--------|
| Q-001 | Should metrics auto-compute on status check or on level complete? | Decided: Both |
| Q-002 | Should we track context_usage time series or just snapshots? | Decided: Snapshots |
