from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mahabharatha.state.persistence import PersistenceLayer


class ResourceRepo:
    """Manages shared resources with concurrency limits and prioritization."""

    def __init__(self, persistence: PersistenceLayer) -> None:
        self._persistence = persistence

    def acquire_slot(
        self, resource_id: str, max_slots: int, worker_id: int, priority: int = 0, timeout_seconds: int = 600
    ) -> bool:
        """Acquire a slot for a resource, waiting if necessary.

        Args:
            resource_id: Identifier for the resource (e.g., 'ollama')
            max_slots: Maximum concurrent slots allowed
            worker_id: ID of the worker requesting the slot
            priority: Higher means more urgent (reserved for future use)
            timeout_seconds: How long to wait before giving up

        Returns:
            True if slot acquired, False if timed out
        """
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            if self._try_acquire(resource_id, max_slots, worker_id):
                return True
            time.sleep(2)  # Wait and retry
        return False

    def _try_acquire(self, resource_id: str, max_slots: int, worker_id: int) -> bool:
        """Atomic check and increment of resource slots."""
        # Use atomic_update for thread and process safety
        with self._persistence.atomic_update():
            # In atomic_update, we use self._persistence.state directly
            resources = self._persistence.state.setdefault("resources", {})
            slots = resources.setdefault(resource_id, {})
            active = slots.get("active", [])

            # For simplicity, if worker already has a slot, just return True
            if worker_id in active:
                return True

            if len(active) < max_slots:
                active.append(worker_id)
                slots["active"] = active
                # atomic_update handles the save() automatically
                return True
            return False

    def release_slot(self, resource_id: str, worker_id: int) -> None:
        """Release a previously acquired slot."""
        with self._persistence.atomic_update():
            resources = self._persistence.state.get("resources", {})
            slots = resources.get(resource_id, {})
            active = slots.get("active", [])

            if worker_id in active:
                active.remove(worker_id)
                slots["active"] = active
                # atomic_update handles the save()
