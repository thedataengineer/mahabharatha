"""MAHABHARATHA v2 Task Graph - Task dependency and execution order management."""

import json
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema


@dataclass
class VerificationConfig:
    """Verification command configuration."""

    command: str
    timeout_seconds: int = 60


@dataclass
class TaskFiles:
    """File ownership for a task."""

    create: list[str]
    modify: list[str]
    read: list[str]


@dataclass
class Task:
    """Individual task definition."""

    id: str
    title: str
    description: str
    level: int
    dependencies: list[str]
    files: TaskFiles
    acceptance_criteria: list[str]
    verification: VerificationConfig
    agents_required: list[str] = field(default_factory=list)


class TaskGraph:
    """Manages task dependencies and execution order."""

    def __init__(self, tasks: list[Task]):
        """Initialize task graph.

        Args:
            tasks: List of tasks to manage
        """
        self.tasks: dict[str, Task] = {t.id: t for t in tasks}
        self._adjacency: dict[str, list[str]] = {}
        self._build_dag()

    @classmethod
    def from_dict(cls, data: dict) -> "TaskGraph":
        """Create TaskGraph from dictionary.

        Args:
            data: Dictionary with task graph data

        Returns:
            TaskGraph instance
        """
        tasks = []
        for t in data.get("tasks", []):
            files = TaskFiles(
                create=t.get("files", {}).get("create", []),
                modify=t.get("files", {}).get("modify", []),
                read=t.get("files", {}).get("read", []),
            )
            verification = VerificationConfig(
                command=t.get("verification", {}).get("command", ""),
                timeout_seconds=t.get("verification", {}).get("timeout_seconds", 60),
            )
            task = Task(
                id=t["id"],
                title=t.get("title", ""),
                description=t.get("description", ""),
                level=t.get("level", 0),
                dependencies=t.get("dependencies", []),
                files=files,
                acceptance_criteria=t.get("acceptance_criteria", []),
                verification=verification,
                agents_required=t.get("agents_required", []),
            )
            tasks.append(task)
        return cls(tasks)

    @classmethod
    def from_file(cls, path: str) -> "TaskGraph":
        """Load and validate task graph from JSON.

        Args:
            path: Path to task-graph.json file

        Returns:
            TaskGraph instance

        Raises:
            FileNotFoundError: If file doesn't exist
            jsonschema.ValidationError: If data is invalid
            ValueError: If circular dependencies detected
        """
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Task graph not found: {path}")

        with open(path_obj) as f:
            data = json.load(f)

        # Validate against schema if available
        schema = load_schema("task-graph.schema.json")
        if schema:
            jsonschema.validate(instance=data, schema=schema)

        return cls.from_dict(data)

    def _build_dag(self) -> None:
        """Build directed acyclic graph from dependencies.

        Raises:
            ValueError: If circular dependencies detected
        """
        # Build adjacency list (task -> tasks that depend on it)
        self._adjacency = {task_id: [] for task_id in self.tasks}
        for task_id, task in self.tasks.items():
            for dep_id in task.dependencies:
                if dep_id in self._adjacency:
                    self._adjacency[dep_id].append(task_id)

        # Detect cycles using DFS with color marking
        cycles = self._detect_cycles()
        if cycles:
            cycle_str = " -> ".join(cycles[0])
            raise ValueError(f"Circular dependency detected: {cycle_str}")

    def _detect_cycles(self) -> list[list[str]]:
        """Detect circular dependencies using DFS.

        Returns:
            List of cycles found (each cycle is a list of task IDs)
        """
        # DFS colors: 0=unvisited, 1=in progress, 2=complete
        unvisited, in_progress, complete = 0, 1, 2
        color: dict[str, int] = dict.fromkeys(self.tasks, unvisited)
        cycles: list[list[str]] = []
        path: list[str] = []

        def dfs(node: str) -> bool:
            color[node] = in_progress
            path.append(node)

            # Check dependencies (edges going TO this node conceptually,
            # but we traverse FROM node to its dependents)
            task = self.tasks[node]
            for dep_id in task.dependencies:
                if dep_id not in self.tasks:
                    continue
                if color[dep_id] == in_progress:
                    # Found cycle - extract it from path
                    cycle_start = path.index(dep_id)
                    cycle = path[cycle_start:] + [dep_id]
                    cycles.append(cycle)
                    return True
                if color[dep_id] == unvisited and dfs(dep_id):
                    return True

            path.pop()
            color[node] = complete
            return False

        for task_id in self.tasks:
            if color[task_id] == unvisited and dfs(task_id):
                break

        return cycles

    def get_level_tasks(self, level: int) -> list[Task]:
        """Get all tasks at specified level.

        Args:
            level: Level number (0-indexed)

        Returns:
            List of tasks at that level
        """
        return [t for t in self.tasks.values() if t.level == level]

    def get_ready_tasks(self, completed: set[str]) -> list[Task]:
        """Get tasks whose dependencies are satisfied.

        Args:
            completed: Set of completed task IDs

        Returns:
            List of tasks ready to execute
        """
        ready = []
        for task in self.tasks.values():
            if task.id in completed:
                continue
            if all(dep in completed for dep in task.dependencies):
                ready.append(task)
        return ready

    def validate_file_ownership(self) -> list[str]:
        """Check for file ownership conflicts.

        Returns:
            List of error messages for conflicts found
        """
        errors: list[str] = []
        file_owners: dict[str, str] = {}

        for task in self.tasks.values():
            for f in task.files.create + task.files.modify:
                if f in file_owners:
                    errors.append(f"File '{f}' owned by both {file_owners[f]} and {task.id}")
                else:
                    file_owners[f] = task.id

        return errors

    @property
    def level_count(self) -> int:
        """Total number of levels in graph."""
        if not self.tasks:
            return 0
        return max(t.level for t in self.tasks.values()) + 1


def load_schema(name: str) -> dict | None:
    """Load JSON schema from schemas directory.

    Args:
        name: Schema filename

    Returns:
        Schema dictionary or None if not found
    """
    schema_path = Path(__file__).parent / "schemas" / name
    if not schema_path.exists():
        return None
    with open(schema_path) as f:
        return json.load(f)
