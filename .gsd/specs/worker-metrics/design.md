# Technical Design: worker-metrics

## Metadata
- **Feature**: worker-metrics
- **Status**: DRAFT
- **Created**: 2026-01-27
- **Author**: MAHABHARATHA Design Mode

---

## 1. Overview

### 1.1 Summary
Add comprehensive metrics tracking to MAHABHARATHA workers, capturing timing data (initialization, task execution, level duration), computing aggregations (averages, percentiles), persisting to state, and displaying in `mahabharatha status`.

### 1.2 Goals
- Track worker initialization and task execution timing
- Compute level-wise and feature-wide aggregations
- Persist metrics for crash recovery
- Surface metrics in status command

### 1.3 Non-Goals
- Prometheus/external metrics export (future)
- Real-time streaming metrics (future)
- CPU/memory resource tracking (future)

---

## 2. Architecture

### 2.1 High-Level Design

```
┌─────────────────┐     ┌─────────────────┐
│   Orchestrator  │────▶│  MetricsCollector│
│  (timestamps)   │     │   (compute)      │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│   StateManager  │◀────│   types.py      │
│  (persist)      │     │   (dataclasses) │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│   status.py     │
│  (display)      │
└─────────────────┘
```

### 2.2 Component Breakdown

| Component | Responsibility | Files |
|-----------|---------------|-------|
| Metric Types | Dataclasses for metrics | `mahabharatha/types.py` |
| MetricsCollector | Compute metrics from state | `mahabharatha/metrics.py` |
| StateManager | Store/retrieve timestamps & metrics | `mahabharatha/state.py` |
| Status Command | Display metrics | `mahabharatha/commands/status.py` |
| State Schema | Validate metrics in state | `.mahabharatha/schemas/state.schema.json` |

### 2.3 Data Flow

1. **Orchestrator** records timestamps when workers spawn/ready, tasks claim/complete
2. **StateManager** persists timestamps to state file
3. **MetricsCollector** reads state, computes duration_ms values and aggregations
4. **Status command** calls MetricsCollector, displays formatted output

---

## 3. Detailed Design

### 3.1 New Types (mahabharatha/types.py)

```python
@dataclass
class WorkerMetrics:
    """Aggregated metrics for a single worker."""
    worker_id: int
    initialization_ms: int | None = None  # ready_at - started_at
    uptime_ms: int = 0                     # now - started_at
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_task_duration_ms: int = 0
    avg_task_duration_ms: float = 0.0

    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "WorkerMetrics": ...


@dataclass
class TaskMetrics:
    """Metrics for a single task execution."""
    task_id: str
    queue_wait_ms: int | None = None       # claimed_at - created_at
    execution_duration_ms: int | None = None  # completed_at - started_at
    verification_duration_ms: int | None = None  # from VerificationResult
    total_duration_ms: int | None = None   # completed_at - created_at

    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "TaskMetrics": ...


@dataclass
class LevelMetrics:
    """Metrics for a level execution."""
    level: int
    duration_ms: int | None = None         # completed_at - started_at
    task_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    avg_task_duration_ms: float = 0.0
    p50_duration_ms: int = 0
    p95_duration_ms: int = 0

    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "LevelMetrics": ...


@dataclass
class FeatureMetrics:
    """Aggregated metrics for entire feature execution."""
    computed_at: datetime
    total_duration_ms: int | None = None
    workers_used: int = 0
    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    levels_completed: int = 0
    worker_metrics: list[WorkerMetrics] = field(default_factory=list)
    level_metrics: list[LevelMetrics] = field(default_factory=list)

    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "FeatureMetrics": ...
```

### 3.2 Extended Types

**WorkerState** - add fields:
```python
ready_at: datetime | None = None           # When worker became ready
last_task_completed_at: datetime | None = None
```

**TaskExecution** (TypedDict) - add fields:
```python
claimed_at: str  # ISO timestamp when task was claimed
duration_ms: int  # Execution duration
```

### 3.3 MetricsCollector (mahabharatha/metrics.py)

```python
class MetricsCollector:
    """Compute and aggregate metrics from state."""

    def __init__(self, state: StateManager) -> None:
        self._state = state

    def compute_worker_metrics(self, worker_id: int) -> WorkerMetrics:
        """Compute metrics for a single worker."""
        ...

    def compute_task_metrics(self, task_id: str) -> TaskMetrics:
        """Compute metrics for a single task."""
        ...

    def compute_level_metrics(self, level: int) -> LevelMetrics:
        """Compute metrics for a level."""
        ...

    def compute_feature_metrics(self) -> FeatureMetrics:
        """Compute all metrics for the feature."""
        ...

    def export_json(self, path: Path) -> None:
        """Export metrics to JSON file."""
        ...


def duration_ms(start: datetime | str | None, end: datetime | str | None) -> int | None:
    """Calculate duration in milliseconds between two timestamps."""
    ...


def calculate_percentile(values: list[int], percentile: int) -> int:
    """Calculate percentile from a list of values."""
    ...
```

### 3.4 StateManager Extensions (mahabharatha/state.py)

New methods:
```python
def record_task_claimed(self, task_id: str, worker_id: int) -> None:
    """Record when a task was claimed (sets claimed_at)."""
    ...

def record_task_duration(self, task_id: str, duration_ms: int) -> None:
    """Record task execution duration."""
    ...

def store_metrics(self, metrics: FeatureMetrics) -> None:
    """Store computed metrics to state."""
    ...

def get_metrics(self) -> FeatureMetrics | None:
    """Retrieve stored metrics."""
    ...
```

### 3.5 State Schema Extension

```json
{
  "definitions": {
    "task": {
      "properties": {
        "claimed_at": {"type": ["string", "null"]},
        "duration_ms": {"type": ["integer", "null"]}
      }
    },
    "worker": {
      "properties": {
        "ready_at": {"type": ["string", "null"]},
        "last_task_completed_at": {"type": ["string", "null"]}
      }
    },
    "metrics": {
      "type": "object",
      "properties": {
        "computed_at": {"type": "string"},
        "total_duration_ms": {"type": ["integer", "null"]},
        "workers_used": {"type": "integer"},
        "tasks_total": {"type": "integer"},
        "tasks_completed": {"type": "integer"},
        "tasks_failed": {"type": "integer"},
        "worker_metrics": {"type": "array"},
        "level_metrics": {"type": "array"}
      }
    }
  },
  "properties": {
    "metrics": {"$ref": "#/definitions/metrics"}
  }
}
```

### 3.6 Status Display

Enhanced output format:
```
MAHABHARATHA Status: worker-metrics
════════════════════════════

Progress: ████████████░░░░░░░░ 60% (6/10 tasks)

Level Status:
  Level 1: ✓ DONE    2m15s (4 tasks, avg=34s, p95=58s)
  Level 2: RUNNING   1m30s (3/5 tasks)
  Level 3: PENDING

Worker Metrics:
┌────────┬───────┬───────┬────────┬───────────┐
│ Worker │ Init  │ Tasks │ Avg    │ Uptime    │
├────────┼───────┼───────┼────────┼───────────┤
│ 0      │ 1.2s  │ 3     │ 45s    │ 4m30s     │
│ 1      │ 1.1s  │ 2     │ 52s    │ 4m28s     │
│ 2      │ 1.3s  │ 1     │ 38s    │ 2m15s     │
└────────┴───────┴───────┴────────┴───────────┘

Total: 4m00s | Workers: 3 | Tasks: 6/10
```

---

## 4. Key Decisions

### Decision: Metrics computation trigger

**Context**: When should metrics be computed?

**Options**:
1. On every status call (always fresh)
2. On level complete only (batched)
3. Both with caching (hybrid)

**Decision**: Option 3 - compute on level complete AND on status call with caching

**Rationale**: Level complete provides checkpoints; status call ensures fresh data

### Decision: Timestamp storage location

**Context**: Where to store new timestamps (ready_at, claimed_at)?

**Options**:
1. Extend existing WorkerState/TaskExecution types
2. Create new MetricTimestamps type
3. Store in metrics section only

**Decision**: Option 1 - extend existing types

**Rationale**: Keeps related data together, minimal schema changes

---

## 5. File Ownership Matrix

| File | Task | Operation | Level |
|------|------|-----------|-------|
| `mahabharatha/types.py` | WM-001 | modify | 1 |
| `mahabharatha/metrics.py` | WM-002 | create | 2 |
| `mahabharatha/state.py` | WM-003 | modify | 2 |
| `.mahabharatha/schemas/state.schema.json` | WM-004 | modify | 2 |
| `mahabharatha/orchestrator.py` | WM-005 | modify | 3 |
| `mahabharatha/commands/status.py` | WM-006 | modify | 3 |
| `tests/unit/test_metrics.py` | WM-007 | create | 4 |
| `tests/integration/test_metrics_integration.py` | WM-008 | create | 4 |

---

## 6. Dependency Graph

```
Level 1:  WM-001 (types)
              │
              ├──────────┬──────────┐
              ▼          ▼          ▼
Level 2:  WM-002    WM-003     WM-004
          metrics   state      schema
              │          │
              └────┬─────┘
                   ▼
Level 3:       WM-005 ────── WM-006
            orchestrator    status
                   │          │
                   └────┬─────┘
                        ▼
Level 4:           WM-007 ── WM-008
                  unit test  integ test
```

---

## 7. Testing Strategy

### 7.1 Unit Tests (test_metrics.py)
- `test_duration_ms_calculation`
- `test_duration_ms_with_none`
- `test_calculate_percentile_p50`
- `test_calculate_percentile_p95`
- `test_calculate_percentile_empty_list`
- `test_worker_metrics_computation`
- `test_task_metrics_computation`
- `test_level_metrics_computation`
- `test_feature_metrics_aggregation`
- `test_metrics_to_dict_from_dict`

### 7.2 Integration Tests (test_metrics_integration.py)
- `test_metrics_persist_to_state`
- `test_metrics_computed_on_level_complete`
- `test_status_displays_metrics`

### 7.3 Verification Commands
```bash
# Unit tests
pytest tests/unit/test_metrics.py -v

# Integration tests
pytest tests/integration/test_metrics_integration.py -v

# Type check
python -c "from mahabharatha.metrics import MetricsCollector"

# Status with metrics
mahabharatha status --feature <feature> --json | jq '.metrics'
```

---

## 8. Parallel Execution Notes

### 8.1 Safe Parallelization
- Level 1: 1 task (types foundation)
- Level 2: 3 tasks (metrics, state, schema) - fully parallel
- Level 3: 2 tasks (orchestrator, status) - fully parallel
- Level 4: 2 tasks (unit, integration tests) - fully parallel

### 8.2 Recommended Workers
- Minimum: 1 worker
- Optimal: 3 workers (matches max level width)
- Maximum: 3 workers (no benefit beyond)

### 8.3 Estimated Duration
- Single worker: ~45 minutes
- With 3 workers: ~25 minutes
- Speedup: 1.8x

---

## 9. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Architecture | | | PENDING |
| Engineering | | | PENDING |
