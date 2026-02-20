# Plugin API Reference

This page documents the abstract base classes, dataclasses, and registry methods that make up the MAHABHARATHA plugin API. For a conceptual overview, see [[Plugin System]].

All plugin types are defined in `mahabharatha/plugins.py`.

---

## Abstract Base Classes

### QualityGatePlugin

Base class for custom quality gate implementations.

**Source:** `mahabharatha/plugins.py`

```python
class QualityGatePlugin(abc.ABC):

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique name identifying this quality gate."""

    @abc.abstractmethod
    def run(self, ctx: GateContext) -> GateRunResult:
        """Execute the quality gate and return the result."""
```

**Contract:**

- `name` must be unique across all registered gates.
- `run()` receives a `GateContext` and must return a `GateRunResult`.
- If `run()` raises an exception, it is caught by the registry and logged. The gate result is set to `GateResult.ERROR`.
- Gates have a 5-minute timeout enforced by the orchestrator (configurable).
- Gates have read-only access to the filesystem and config.

---

### LifecycleHookPlugin

Base class for lifecycle event observers.

**Source:** `mahabharatha/plugins.py`

```python
class LifecycleHookPlugin(abc.ABC):

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique name identifying this lifecycle hook."""

    @abc.abstractmethod
    def on_event(self, event: LifecycleEvent) -> None:
        """Handle a lifecycle event."""
```

**Contract:**

- `on_event()` is called for every lifecycle event type when registered via entry points.
- The method must not block. Long-running operations should be dispatched asynchronously.
- Exceptions are caught and logged. A failing hook does not prevent other hooks from running.
- Hooks have no access to mutable orchestrator state.

---

### LauncherPlugin

Base class for custom worker execution environments.

**Source:** `mahabharatha/plugins.py`

```python
class LauncherPlugin(abc.ABC):

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique name identifying this launcher."""

    @abc.abstractmethod
    def create_launcher(self, config: Any) -> Any:
        """Create and return a WorkerLauncher instance from the given config."""
```

**Contract:**

- `name` is referenced in `workers.launcher_type` in the config YAML.
- `create_launcher()` receives the full MAHABHARATHA config and must return an object implementing the `WorkerLauncher` ABC from `mahabharatha/launcher.py`.
- The returned launcher must implement three methods: `launch()`, `wait()`, and `cleanup()`.

---

### ContextPlugin

Base class for context engineering plugins that inject task-scoped context into worker prompts.

**Source:** `mahabharatha/plugins.py`

```python
class ContextPlugin(abc.ABC):

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique name identifying this context plugin."""

    @abc.abstractmethod
    def build_task_context(self, task: dict, task_graph: dict, feature: str) -> str:
        """Build context string for a specific task.

        Args:
            task: Task dict from task-graph.json
            task_graph: Full task graph dict
            feature: Feature name

        Returns:
            Markdown context string to inject into worker prompt.
            Return empty string to signal fallback to full context.
        """

    @abc.abstractmethod
    def estimate_context_tokens(self, task: dict) -> int:
        """Estimate token count for task context."""
```

**Contract:**

- `build_task_context()` is called for each task before the worker starts.
- Multiple context plugins can be registered. Their outputs are concatenated with `---` separators.
- Exceptions are caught per-plugin. A failing plugin does not prevent others from contributing.
- Return an empty string to signal that the caller should fall back to full/global context.

---

## Dataclasses

### GateContext

Context object passed to quality gate `run()` methods.

**Source:** `mahabharatha/plugins.py`

```python
@dataclass
class GateContext:
    feature: str     # Feature name being built
    level: int       # Level number that was just merged
    cwd: Path        # Working directory (project root)
    config: Any      # Full ZergConfig object
```

### LifecycleEvent

Event object passed to lifecycle hook `on_event()` methods.

**Source:** `mahabharatha/plugins.py`

```python
@dataclass
class LifecycleEvent:
    event_type: str                   # Event name (see event table)
    data: dict[str, Any]              # Event-specific payload
    timestamp: datetime = field(      # When the event occurred
        default_factory=datetime.now
    )
```

### GateRunResult

Return type for quality gate `run()` methods.

**Source:** `mahabharatha/types.py`

```python
@dataclass
class GateRunResult:
    gate_name: str        # Name of the gate that ran
    result: GateResult    # PASS, FAIL, SKIP, TIMEOUT, or ERROR
    command: str          # Command that was executed
    exit_code: int        # Process exit code
    stdout: str = ""      # Standard output
    stderr: str = ""      # Standard error
```

### GateResult (Enum)

**Source:** `mahabharatha/constants.py`

| Value | Meaning |
|-------|---------|
| `PASS` | Gate validation succeeded |
| `FAIL` | Gate validation found issues |
| `SKIP` | Gate was skipped (not applicable) |
| `TIMEOUT` | Gate exceeded its timeout |
| `ERROR` | Gate raised an unexpected exception |

---

## PluginRegistry

The central registry for discovering, registering, and dispatching plugins.

**Source:** `mahabharatha/plugins.py`

### Registration Methods

```python
class PluginRegistry:
    def register_hook(self, event_type: str, callback: Callable) -> None
    def register_gate(self, plugin: QualityGatePlugin, required: bool = True) -> None
    def register_launcher(self, plugin: LauncherPlugin) -> None
    def register_context_plugin(self, plugin: ContextPlugin) -> None
```

| Method | Parameters | Description |
|--------|-----------|-------------|
| `register_hook` | `event_type`: event name; `callback`: callable accepting `LifecycleEvent` | Register a callback for a specific event type |
| `register_gate` | `plugin`: QualityGatePlugin instance; `required`: whether failure blocks merge | Register a quality gate plugin |
| `register_launcher` | `plugin`: LauncherPlugin instance | Register a launcher plugin by its name |
| `register_context_plugin` | `plugin`: ContextPlugin instance | Register a context engineering plugin |

### Dispatch Methods

```python
class PluginRegistry:
    def emit_event(self, event: LifecycleEvent) -> None
    def run_plugin_gate(self, name: str, ctx: GateContext) -> GateRunResult
    def get_launcher(self, name: str) -> LauncherPlugin | None
    def is_gate_required(self, name: str) -> bool
    def get_context_plugins(self) -> list[ContextPlugin]
    def build_task_context(self, task: dict, task_graph: dict, feature: str) -> str
```

| Method | Returns | Description |
|--------|---------|-------------|
| `emit_event` | None | Dispatches an event to all registered hooks for that event type. Exceptions are caught per-hook. |
| `run_plugin_gate` | `GateRunResult` | Runs a named gate. Returns `ERROR` result if the gate is not found or raises. |
| `get_launcher` | `LauncherPlugin` or `None` | Looks up a launcher by name. |
| `is_gate_required` | `bool` | Checks whether a gate was registered with `required=True`. Defaults to True if not found. |
| `get_context_plugins` | `list[ContextPlugin]` | Returns all registered context plugins. |
| `build_task_context` | `str` | Calls all context plugins and concatenates their output with `---` separators. |

### Loading Methods

```python
class PluginRegistry:
    def load_yaml_hooks(self, hooks_config: list[dict]) -> None
    def load_entry_points(self, group: str = "mahabharatha.plugins") -> None
```

| Method | Parameters | Description |
|--------|-----------|-------------|
| `load_yaml_hooks` | `hooks_config`: list of dicts with `event` and `command` keys | Converts YAML hook definitions into registered callbacks. Commands are parsed with `shlex.split` and executed via `subprocess.run` (no shell). |
| `load_entry_points` | `group`: entry point group name | Discovers plugins from installed packages. Instantiates each entry point class and registers it based on its ABC type. |

---

## Plugin Configuration Models

Configuration models are defined in `mahabharatha/plugin_config.py` using Pydantic.

### HookConfig

```python
class HookConfig(BaseModel):
    event: str     # Lifecycle event name
    command: str   # Shell command to execute
    timeout: int = 60  # 1-600 seconds
```

### PluginGateConfig

```python
class PluginGateConfig(BaseModel):
    name: str          # Unique gate name
    command: str       # Shell command to execute
    required: bool = False   # Whether failure blocks merge
    timeout: int = 300       # 1-3600 seconds
```

### LauncherPluginConfig

```python
class LauncherPluginConfig(BaseModel):
    name: str           # Launcher name (e.g., "k8s")
    entry_point: str    # Python entry point (e.g., "my_pkg:K8sLauncher")
```

### ContextEngineeringConfig

```python
class ContextEngineeringConfig(BaseModel):
    enabled: bool = True
    command_splitting: bool = True
    security_rule_filtering: bool = True
    task_context_budget_tokens: int = 4000  # 500-20000
    fallback_to_full: bool = True
```

### PluginsConfig

Top-level plugin configuration that appears under `plugins:` in config.yaml.

```python
class PluginsConfig(BaseModel):
    enabled: bool = True
    hooks: list[HookConfig] = []
    quality_gates: list[PluginGateConfig] = []
    launchers: list[LauncherPluginConfig] = []
    context_engineering: ContextEngineeringConfig = ContextEngineeringConfig()
```

---

## Entry Point Registration

To distribute a plugin as an installable package, declare entry points in `pyproject.toml`:

```toml
[project.entry-points."mahabharatha.plugins"]
my-security-gate = "my_package.gates:SecurityScanGate"
my-slack-hook = "my_package.hooks:SlackNotifier"
my-k8s-launcher = "my_package.launchers:K8sLauncherPlugin"
my-context = "my_package.context:CustomContextPlugin"
```

Each entry point must reference a class that:

1. Inherits from exactly one of the four ABC types.
2. Can be instantiated with no arguments (zero-arg constructor).
3. Implements all abstract methods.

The registry auto-detects the plugin type using `isinstance` checks and registers accordingly.

---

## Complete Plugin Example

The following example implements a quality gate that checks for TODO comments in modified files:

```python
# my_plugin/gates.py
import subprocess
from mahabharatha.plugins import QualityGatePlugin, GateContext
from mahabharatha.types import GateRunResult
from mahabharatha.constants import GateResult


class TodoCheckGate(QualityGatePlugin):
    """Fail if any TODO comments exist in the codebase."""

    @property
    def name(self) -> str:
        return "todo-check"

    def run(self, ctx: GateContext) -> GateRunResult:
        cmd = ["grep", "-rn", "TODO", str(ctx.cwd / "src")]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            # grep found matches -- gate fails
            return GateRunResult(
                gate_name=self.name,
                result=GateResult.FAIL,
                command=" ".join(cmd),
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

        # grep found no matches -- gate passes
        return GateRunResult(
            gate_name=self.name,
            result=GateResult.PASS,
            command=" ".join(cmd),
            exit_code=0,
            stdout="No TODO comments found",
            stderr="",
        )
```

Register it in `pyproject.toml`:

```toml
[project.entry-points."mahabharatha.plugins"]
todo-check = "my_plugin.gates:TodoCheckGate"
```

Or in YAML (as a shell command equivalent):

```yaml
plugins:
  quality_gates:
    - name: todo-check
      command: "! grep -rn TODO src/"
      required: false
      timeout: 60
```

---

## See Also

- [[Plugin System]] -- Conceptual overview and usage patterns
- [[Configuration]] -- YAML configuration reference
- [[Context Engineering]] -- Built-in context engineering plugin details
