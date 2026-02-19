"""Governance and Peer Monitoring Service for ZERG.

Handles pulse checks, peer-monitoring logic, and automated task reassignment
for stalled workers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from mahabharatha.heartbeat import HeartbeatMonitor
from mahabharatha.logging import get_logger

if TYPE_CHECKING:
    from mahabharatha.state.manager import StateManager

logger = get_logger("governance")


class GovernanceService:
    """Automated governance for the worker grid."""

    def __init__(self, state_manager: StateManager) -> None:
        self.state = state_manager
        self.monitor = HeartbeatMonitor(state_manager.state_dir)
        # Tracks the last seen narrative to detect stalled 'thinking'
        self._last_narratives: dict[int, str] = {}
        self._last_narrative_times: dict[int, datetime] = {}

        # Enforcement Agency
        charter_path = Path(".gsd/TEAM_CHARTER.md")
        self.enforcer = CharterEnforcer(charter_path)

    def audit_level(self, completion_summaries: dict[str, str]) -> dict[str, str]:
        """Audit all task completions in a level for charter compliance.

        Returns:
            Dict mapping task_id -> violation_message (empty if compliant).
        """
        results = {}
        for tid, summary in completion_summaries.items():
            compliant, reason = self.enforcer.audit_completion(summary)
            if not compliant:
                results[tid] = reason
        return results

    def run_pulse_check(self, worker_ids: list[int]) -> list[int]:
        """Perform a pulse check on all active workers.

        Returns:
            List of worker IDs that failed the governance check (stalled).
        """
        stalled_workers = []
        now = datetime.now(UTC)

        for wid in worker_ids:
            hb = self.monitor.read(wid)
            if not hb:
                logger.warning(f"Governance: Worker {wid} has no heartbeat.")
                stalled_workers.append(wid)
                continue

            # 1. Standard heartbeat staleness (time-based)
            if hb.is_stale(self.monitor.stale_timeout_seconds):
                logger.warning(f"Governance: Worker {wid} heartbeat is stale.")
                stalled_workers.append(wid)
                continue

            # 2. Sentient Narrative Check (content-based)
            # If the narrative hasn't changed for 2x the standard timeout,
            # we consider it a 'cognitive stall' even if the pulse is active.
            narrative = hb.activity_narrative or ""
            last_narrative = self._last_narratives.get(wid)

            if narrative != last_narrative:
                self._last_narratives[wid] = narrative
                self._last_narrative_times[wid] = now
            else:
                last_time = self._last_narrative_times.get(wid, now)
                stall_duration = (now - last_time).total_seconds()

                # Cognitive stall threshold (e.g., 5 minutes)
                if stall_duration > (self.monitor.stale_timeout_seconds * 2.5):
                    logger.warning(
                        f"Governance: Worker {wid} ('{hb.persona_name}') has a cognitive stall. "
                        f"Narrative: '{narrative}'"
                    )
                    stalled_workers.append(wid)

        return stalled_workers

    def perform_peer_reassignment(self, stalled_workers: list[int]) -> None:
        """Handle reassignment for stalled workers."""
        if not stalled_workers:
            return

        for wid in stalled_workers:
            # Placeholder for actual reassignment logic in orchestrator.py
            # This Service identifies the failure; the Orchestrator executes the fix.
            logger.info(f"Governance: Recommendation - Reassign tasks from worker {wid}")


class CharterEnforcer:
    """Enforcement agency for the Team Charter."""

    def __init__(self, charter_path: Path):
        self.charter_path = charter_path
        self._principles = []
        self._load_charter()

    def _load_charter(self):
        if not self.charter_path.exists():
            return
        content = self.charter_path.read_text()
        # Simple extraction of points under 'Core Principles'
        in_principles = False
        for line in content.splitlines():
            if "## Core Principles" in line:
                in_principles = True
                continue
            if line.startswith("##"):
                in_principles = False
            if in_principles and line.strip().startswith("-"):
                self._principles.append(line.strip("- ").strip())

    def audit_completion(self, completion_text: str) -> tuple[bool, str]:
        """Audit a worker's completion report against charter principles.

        Returns:
            (is_compliant, reason_if_any)
        """
        # Sentient compliance check:
        # In a full implementation, this calls an LLM (Yudhishthira)
        # to cross-reference completion_text with self._principles.
        # For now, we perform keyword-based heuristic checks.

        violations = []
        for p in self._principles:
            # Case-insensitive check for key requirements like 'test' or 'doc'
            p_lower = p.lower()
            if "test" in p_lower:
                if "test" not in completion_text.lower():
                    violations.append(f"Violation of Principle: '{p}' (No testing evidence found)")
            elif "doc" in p_lower:
                if "doc" not in completion_text.lower() and "artifact" not in completion_text.lower():
                    violations.append(f"Violation of Principle: '{p}' (No documentation evidence found)")

        if violations:
            return False, "; ".join(violations)
        return True, "Compliant"
