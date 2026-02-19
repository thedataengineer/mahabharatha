"""Persistent Knowledge Service for ZERG.

Aggregates code-level structural data and high-level requirements/decisions.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from mahabharatha.constants import STATE_DIR
from mahabharatha.repo_map import build_map

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeVault:
    """Persistent storage for the repository's 'memory'."""

    root: Path
    knowledge_dir: Path = field(init=False)
    graph_path: Path = field(init=False)
    decisions_path: Path = field(init=False)

    def __post_init__(self) -> None:
        self.knowledge_dir = Path(STATE_DIR) / "knowledge"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.graph_path = self.knowledge_dir / "structural_graph.json"
        self.decisions_path = self.knowledge_dir / "decisions.json"

    def sync_code_graph(self) -> None:
        """Update and persist the structural graph from the current codebase."""
        logger.info("Syncing persistent structural graph...")
        graph = build_map(self.root)

        # Convert to serializable dict
        data = {
            "modules": {mod: [asdict(s) for s in syms] for mod, syms in graph.modules.items()},
            "edges": [asdict(e) for e in graph.edges],
        }

        with open(self.graph_path, "w") as f:
            json.dump(data, f, indent=2)

    def store_decision(self, feature: str, decision: str, rationale: str) -> None:
        """Store an architectural or technical decision."""
        decisions = self._load_decisions()
        decisions.append(
            {
                "feature": feature,
                "decision": decision,
                "rationale": rationale,
                "timestamp": Path().stat().st_mtime,  # Placeholder for actual time if needed
            }
        )
        with open(self.decisions_path, "w") as f:
            json.dump(decisions, f, indent=2)

    def query(self, keywords: list[str]) -> str:
        """Query the vault for relevant historical context."""
        # Simple keyword search in decisions for now
        decisions = self._load_decisions()
        relevant = []
        kw_set = {kw.lower() for kw in keywords}

        for d in decisions:
            text = f"{d['decision']} {d['rationale']}".lower()
            if any(kw in text for kw in kw_set):
                relevant.append(f"- Feature {d['feature']}: {d['decision']} ({d['rationale']})")

        if not relevant:
            return "No relevant historical decisions found."

        return "### Historical Decisions\n" + "\n".join(relevant)

    def _load_decisions(self) -> list[dict[str, Any]]:
        if not self.decisions_path.exists():
            return []
        try:
            with open(self.decisions_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []


class KnowledgeService:
    """Facade for interacting with the Knowledge Vault."""

    def __init__(self, root: str | Path) -> None:
        self.vault = KnowledgeVault(Path(root).resolve())

    def sync(self) -> None:
        """Sync all knowledge subsystems."""
        self.vault.sync_code_graph()

    def add_decision(self, feature: str, decision: str, rationale: str) -> None:
        """Record a decision."""
        self.vault.store_decision(feature, decision, rationale)

    def get_context(self, keywords: list[str]) -> str:
        """Retrieve context for a new task."""
        return self.vault.query(keywords)
