# Plan: Build MAHABHARATHA Container for Dogfooding

**Goal**: Build Docker container with Claude Code, enable both host-based development and container-based development workflows.

**Created**: 2026-01-27

---

## Current State

| Component | Status |
|-----------|--------|
| Dockerfile | ✅ Ready (Claude Code installed via npm) |
| docker-compose.yaml | ✅ Ready (workspace + mahabharatha-worker services) |
| ContainerLauncher | ✅ Implemented (expects image: `mahabharatha-worker`) |
| worker_entry.sh | ✅ Ready |
| Kurukshetra --mode flag | ✅ Implemented |

**Gap**: Image not built. ContainerLauncher expects `mahabharatha-worker` image to exist.

---

## Implementation Steps

### Step 1: Build the Docker Image

```bash
docker build -t mahabharatha-worker -f .devcontainer/Dockerfile .
```

Image includes: Ubuntu + Python 3.12 + Node.js 20 + Claude Code CLI + MCP servers

### Step 2: Verify Claude Code in Container

```bash
docker run --rm -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY mahabharatha-worker claude --version
```

### Step 3: Test Container Launcher

```bash
mahabharatha kurukshetra --mode container --dry-run
```

---

## Workflow A: Host Machine + Container Workers

Run Claude Code on Mac, spawn workers in containers:

```bash
# Your main session (Mac)
claude

# Inside session, kurukshetra spawns container workers
/mahabharatha:plan my-feature
/mahabharatha:design
/mahabharatha:kurukshetra --mode container --workers 3
```

---

## Workflow B: Full Container Development

Run everything inside containers:

```bash
# Start development container
docker-compose -f .devcontainer/docker-compose.yaml up -d workspace

# Enter container
docker-compose -f .devcontainer/docker-compose.yaml exec workspace bash

# Inside container - run Claude Code
claude

# From inside, kurukshetra can spawn sibling containers (requires docker socket mount)
```

**Note**: For Workflow B to spawn worker containers, need Docker-in-Docker or socket mount. Current docker-compose.yaml has `privileged: true` which enables this.

---

## Quick Reference

| Command | Effect |
|---------|--------|
| `mahabharatha kurukshetra --mode container` | Force container workers |
| `mahabharatha kurukshetra --mode subprocess` | Force local subprocess workers |
| `mahabharatha kurukshetra --mode auto` | Auto-detect (default) |
| `mahabharatha kurukshetra --dry-run` | Preview without executing |

---

## Files Involved

| File | Role |
|------|------|
| `.devcontainer/Dockerfile` | Image definition |
| `.devcontainer/docker-compose.yaml` | Multi-container orchestration |
| `.mahabharatha/worker_entry.sh` | Container startup script |
| `mahabharatha/launcher.py:544-700` | ContainerLauncher class |
| `mahabharatha/orchestrator.py:87-177` | Launcher auto-detection |

---

## Verification

1. **Image exists**: `docker images | grep mahabharatha-worker`
2. **Claude works**: `docker run --rm mahabharatha-worker claude --version`
3. **Launcher detects**: `mahabharatha kurukshetra --mode container --dry-run` shows "container mode"
4. **Full test**: Create test feature, run `mahabharatha kurukshetra --mode container --workers 2`

---

## Known Limitations

- `wait-for-services.sh` not implemented (only needed for postgres/redis profiles)
- DC-012 integration test still pending
- Container workers need `ANTHROPIC_API_KEY` in environment
