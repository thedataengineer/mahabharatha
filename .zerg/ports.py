"""MAHABHARATHA v2 Port Allocator - Ephemeral port management for worker isolation."""

import random
import socket
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PortAssignment:
    """Represents a port assignment."""

    port: int
    worker_id: str
    assigned_at: datetime


class PortAllocator:
    """Manages port allocation for workers.

    Allocates ports in the ephemeral range (49152-65535) for worker MCP servers.
    """

    EPHEMERAL_START = 49152
    EPHEMERAL_END = 65535

    def __init__(self):
        """Initialize port allocator."""
        self.assignments: dict[str, PortAssignment] = {}
        self.used_ports: set[int] = set()

    def allocate(self, worker_id: str) -> int:
        """Allocate a port for a worker.

        If the worker already has a port assigned, returns the existing port.

        Args:
            worker_id: Unique identifier for the worker

        Returns:
            Allocated port number

        Raises:
            RuntimeError: If no ports are available
        """
        if worker_id in self.assignments:
            return self.assignments[worker_id].port

        port = self._find_available_port()
        assignment = PortAssignment(
            port=port, worker_id=worker_id, assigned_at=datetime.now()
        )
        self.assignments[worker_id] = assignment
        self.used_ports.add(port)
        return port

    def release(self, worker_id: str) -> None:
        """Release a worker's port.

        Args:
            worker_id: Worker whose port to release
        """
        if worker_id in self.assignments:
            port = self.assignments[worker_id].port
            self.used_ports.discard(port)
            del self.assignments[worker_id]

    def get_assignment(self, worker_id: str) -> PortAssignment | None:
        """Get port assignment for a worker.

        Args:
            worker_id: Worker to look up

        Returns:
            PortAssignment if found, None otherwise
        """
        return self.assignments.get(worker_id)

    def _find_available_port(self) -> int:
        """Find an available port in the ephemeral range.

        Returns:
            Available port number

        Raises:
            RuntimeError: If no ports are available after max attempts
        """
        max_attempts = 100

        for _ in range(max_attempts):
            port = random.randint(self.EPHEMERAL_START, self.EPHEMERAL_END)
            if port not in self.used_ports and self._is_port_available(port):
                return port

        raise RuntimeError("No available ports in ephemeral range")

    def _is_port_available(self, port: int) -> bool:
        """Check if port is available on the system.

        Args:
            port: Port number to check

        Returns:
            True if port is available, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return True
        except OSError:
            return False
