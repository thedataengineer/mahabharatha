# Technical Design: container-execution

## Metadata
- **Feature**: container-execution
- **Status**: REVIEW
- **Created**: 2026-01-28
- **Author**: ZERG Design Mode

---

## 1. Overview

### 1.1 Summary
Wire resource limits into the ContainerLauncher docker run command, harden the Dockerfile for multi-platform builds, add orphan cleanup and health checks to the orchestrator, add container log support to the logs command, remove privileged mode from docker-compose.yaml, and add a `zerg build --docker` flag to build the worker image. All changes preserve the existing ContainerLauncher API and SubprocessLauncher path.

### 1.2 Goals
- Container workers execute with memory/CPU limits from config
- Docker image builds and runs on macOS ARM64 and Linux x86_64
- Orchestrator cleans up orphan containers on startup and detects stuck workers
- `zerg logs` shows container worker output
- `zerg build --docker` builds the worker image
- Security hardened (no privileged, non-root, constrained mounts)

### 1.3 Non-Goals
- Docker-in-Docker (workspace spawning sibling containers)
- docker-compose orchestration (keep docker run)
- Dynamic devcontainer generation integration
- Kubernetes support

---

## 2. Architecture

### 2.1 Data Flow

```
User: zerg rush --mode container --workers 3
  |
  v
Orchestrator._create_launcher(mode="container")
  |
  +--> _auto_detect_launcher_type() -> CONTAINER
  +--> ContainerLauncher(config, image_name, resource_limits)
  |
  v
ContainerLauncher.spawn(worker_id, feature, worktree, branch)
  |
  +--> _start_container(name, worktree, env, resource_limits)
  |      |
  |      +--> docker run -d --memory 4g --cpus 2 ... zerg-worker
  |      +--> _wait_ready() -> container running
  |      +--> _exec_worker_entry() -> worker_entry.sh
  |      +--> _verify_worker_process() -> pgrep worker_main
  |
  v
Orchestrator._poll_workers()
  |
  +--> state.load()  [IPC - already implemented]
  +--> launcher.monitor(worker_id) -> docker inspect
  +--> _health_check_containers() -> timeout detection
  |
  v
Orchestrator._cleanup_containers()  [on exit or startup]
  |
  +--> docker ps -a --filter name=zerg-worker -> orphans
  +--> docker rm -f <orphans>
```

### 2.2 Component Changes

| Component | File | Change |
|-----------|------|--------|
| Resource limits | `zerg/launcher.py` | Pass --memory/--cpus to docker run |
| Config schema | `zerg/config.py` | Add container resource fields to ResourcesConfig |
| Orchestrator | `zerg/orchestrator.py` | Orphan cleanup on init, health check in poll |
| Dockerfile | `.devcontainer/Dockerfile` | Multi-platform, layer optimization |
| docker-compose | `.devcontainer/docker-compose.yaml` | Remove privileged: true |
| Logs command | `zerg/commands/logs.py` | Add docker logs fallback |
| Build command | `zerg/commands/build.py` | Add --docker flag |
| worker_entry.sh | `.zerg/worker_entry.sh` | Add healthcheck marker file |

---

## 3. Detailed Design

### 3.1 Resource Limits in ContainerLauncher

Add `resource_limits` to `__init__` and pass to `_start_container`:

```python
# launcher.py - ContainerLauncher.__init__
def __init__(self, config=None, image_name="zerg-worker", network=None,
             memory_limit="4g", cpu_limit=2.0):
    ...
    self.memory_limit = memory_limit
    self.cpu_limit = cpu_limit

# launcher.py - _start_container
# After network flag, before env vars:
cmd.extend(["--memory", self.memory_limit])
cmd.extend(["--cpus", str(self.cpu_limit)])
```

### 3.2 Config Schema Extension

```python
# config.py - ResourcesConfig (extend existing)
class ResourcesConfig(BaseModel):
    cpu_cores: int = 2
    memory_gb: int = 4
    disk_gb: int = 10
    container_memory_limit: str = "4g"   # Docker format
    container_cpu_limit: float = 2.0     # Docker --cpus value
```

### 3.3 Orchestrator Enhancements

```python
# orchestrator.py - __init__: add cleanup call
def __init__(self, ...):
    ...
    self._cleanup_orphan_containers()

# New method
def _cleanup_orphan_containers(self):
    """Remove leftover zerg-worker containers from previous runs."""
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=zerg-worker",
             "--format", "{{.ID}}"],
            capture_output=True, text=True, timeout=10)
        for cid in result.stdout.strip().split("\n"):
            if cid:
                subprocess.run(["docker", "rm", "-f", cid], ...)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # Docker not available, skip
```

### 3.4 Health Check in Poll Loop

```python
# orchestrator.py - _poll_workers: add after state.load()
def _check_container_health(self):
    """Mark containers stuck beyond timeout as CRASHED."""
    for wid, handle in self.launcher.get_all_workers().items():
        if handle.status == WorkerStatus.RUNNING:
            ws = self.state.get_worker_state(wid)
            if ws and ws.started_at:
                elapsed = (datetime.now() - ws.started_at).total_seconds()
                if elapsed > self.config.workers.timeout:
                    self.launcher.terminate(wid)
                    # State will be updated to CRASHED by monitor()
```

### 3.5 Docker Log Collection

```python
# logs.py - add container log fetching
def _get_container_logs(worker_id: int) -> str | None:
    """Fetch logs from a running or stopped container."""
    name = f"zerg-worker-{worker_id}"
    try:
        result = subprocess.run(
            ["docker", "logs", name],
            capture_output=True, text=True, timeout=10)
        return result.stdout if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
```

### 3.6 Build --docker Flag

```python
# build.py - add docker build support
@click.option("--docker", is_flag=True, help="Build the zerg-worker Docker image")
def build(docker, ...):
    if docker:
        _build_docker_image()
        return
    ...

def _build_docker_image():
    """Build the zerg-worker Docker image."""
    dockerfile = Path(".devcontainer/Dockerfile")
    if not dockerfile.exists():
        console.print("[red]No .devcontainer/Dockerfile found[/red]")
        raise SystemExit(1)
    cmd = ["docker", "build", "-t", "zerg-worker", "-f", str(dockerfile), "."]
    result = subprocess.run(cmd, timeout=600)
    if result.returncode == 0:
        console.print("[green]Image built: zerg-worker[/green]")
    else:
        console.print("[red]Build failed[/red]")
        raise SystemExit(1)
```

### 3.7 Dockerfile Hardening

```dockerfile
# Multi-stage for smaller image, explicit platform
FROM --platform=$BUILDPLATFORM mcr.microsoft.com/devcontainers/base:ubuntu AS base
# ... existing content ...
# Add HEALTHCHECK
HEALTHCHECK --interval=30s --timeout=5s CMD test -f /tmp/.zerg-alive || exit 1
```

### 3.8 docker-compose.yaml Security Fix

Remove `privileged: true` from workspace service. Add explicit capabilities only if needed for Docker socket access (deferred — out of scope).

---

## 4. Key Decisions

### Decision: docker run with --memory/--cpus vs ResourceLimits dataclass

**Context**: ContainerLauncher needs resource limits. A ResourceLimits dataclass exists in `.zerg/container.py` but isn't wired to the active launcher.

**Options**:
1. Reuse `.zerg/container.py` ResourceLimits — adds import dependency on inactive module
2. Add fields directly to ContainerLauncher — simpler, self-contained
3. Add to config.py ResourcesConfig — centralized, matches existing pattern

**Decision**: Option 3 — extend ResourcesConfig with container_memory_limit and container_cpu_limit fields, pass from orchestrator to launcher.

**Rationale**: Config is the canonical source of truth. Orchestrator already reads config. Keeps launcher simple (just receives values).

### Decision: Orphan cleanup timing

**Context**: Orphan containers from crashed orchestrators need cleanup.

**Options**:
1. Cleanup at orchestrator init — catches all orphans before starting
2. Cleanup at rush start — only when explicitly launching
3. Both

**Decision**: Option 1 — cleanup at orchestrator init. Any time the orchestrator starts, it should ensure a clean state.

---

## 5. Implementation Plan

### 5.1 Phase Summary

| Phase | Level | Tasks | Parallel |
|-------|-------|-------|----------|
| Foundation | L1 | 3 | Yes |
| Core | L2 | 3 | Yes |
| Integration | L3 | 2 | Yes |
| Testing | L4 | 2 | Yes |
| Verification | L5 | 1 | No |

### 5.2 File Ownership

| File | Task ID | Operation |
|------|---------|-----------|
| `zerg/config.py` | CE-L1-001 | modify |
| `.zerg/config.yaml` | CE-L1-001 | modify |
| `.devcontainer/Dockerfile` | CE-L1-002 | modify |
| `.devcontainer/docker-compose.yaml` | CE-L1-003 | modify |
| `zerg/launcher.py` | CE-L2-001 | modify |
| `zerg/orchestrator.py` | CE-L2-002 | modify |
| `zerg/commands/logs.py` | CE-L2-003 | modify |
| `zerg/commands/build.py` | CE-L3-001 | modify |
| `.zerg/worker_entry.sh` | CE-L3-002 | modify |
| `tests/unit/test_container_resources.py` | CE-L4-001 | create |
| `tests/integration/test_container_e2e_live.py` | CE-L4-002 | create |

### 5.3 Dependency Graph

```
L1: CE-L1-001 (config)     CE-L1-002 (Dockerfile)     CE-L1-003 (compose)
         |                       |                           |
         v                       v                           |
L2: CE-L2-001 (launcher) CE-L2-002 (orchestrator)  CE-L2-003 (logs)
         |                       |                           |
         v                       v                           |
L3:         CE-L3-001 (build cmd)       CE-L3-002 (entry.sh)|
                  |                           |              |
                  v                           v              v
L4:    CE-L4-001 (unit tests)      CE-L4-002 (integration tests)
                  |                           |
                  v                           v
L5:              CE-L5-001 (full suite + lint)
```

---

## 6. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Docker not installed on user machine | Medium | High | Auto-detect falls back to subprocess |
| Git worktree paths break in container | Medium | High | worker_entry.sh already handles; add integration test |
| OAuth token format changes between host/container | Low | High | Mount ~/.claude read-write; test explicitly |
| Resource limits too restrictive for Claude Code | Low | Medium | Default 4G/2CPU is generous; make configurable |
| Orphan cleanup removes containers from other tools | Low | Medium | Filter by name prefix zerg-worker |

---

## 7. Testing Strategy

### 7.1 Unit Tests (CE-L4-001)
- Config loads container resource fields correctly
- ContainerLauncher._start_container includes --memory/--cpus flags
- Orchestrator._cleanup_orphan_containers handles no-docker gracefully
- Health check logic with mock timestamps
- Logs command falls back to docker logs

### 7.2 Integration Tests (CE-L4-002)
- Docker image builds (requires Docker)
- Container spawns with resource limits (verify via docker inspect)
- Orphan cleanup removes stale containers
- Container log collection works

### 7.3 Gating
- Integration tests gated on `@pytest.mark.skipif(not docker_available())`
- Full E2E dogfood is manual (TC-003 from requirements)

---

## 8. Parallel Execution Notes

### 8.1 Recommended Workers
- Minimum: 1 worker (sequential)
- Optimal: 3 workers (L1 has 3 independent tasks)
- Maximum: 3 workers (widest level is 3)

### 8.2 Estimated Duration
- Single worker: ~11 tasks sequential
- With 3 workers: L1(3 parallel) + L2(3 parallel) + L3(2 parallel) + L4(2 parallel) + L5(1)

---

## 9. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Architecture | | | PENDING |
| Engineering | | | PENDING |
