"""Verification script for MAHABHARATHA Sentient Expansion."""

import sys
from pathlib import Path

# Add repo to path
sys.path.append(str(Path.cwd()))

from mahabharatha.charter import TeamCharter, write_team_charter_md
from mahabharatha.heartbeat import Heartbeat
from mahabharatha.knowledge import KnowledgeService
from mahabharatha.persona import get_theme


def verify():
    print("--- Verifying Persona System ---")
    theme = get_theme("pandava")
    print(f"Theme: {theme.name}")
    for role in theme.roles:
        print(f"Role: {role.name} - {role.description}")

    print("\n--- Verifying Knowledge Service ---")
    ks = KnowledgeService(".")
    ks.sync()
    print("Knowledge synced (Check .mahabharatha/state/knowledge/structural_graph.json)")
    ks.add_decision("Sentient Expansion", "Integrated Pandava Theme", "User requested character-driven orchestration")
    print("Decision stored.")

    print("\n--- Verifying Heartbeat Narrative ---")
    hb = Heartbeat(
        worker_id=1,
        timestamp="2026-02-11T20:15:00Z",
        task_id="task-001",
        step="implementing",
        progress_pct=50,
        activity_narrative="Writing the core logic for the Persona module.",
        persona_name="Arjuna",
    )
    print(f"Heartbeat: {hb.persona_name} is {hb.activity_narrative}")

    print("\n--- Verifying Team Charter ---")
    tc = TeamCharter(
        mission="Build the future of agentic coding.", theme_name="pandava", principles=["Honor", "Speed", "Truth"]
    )
    path = write_team_charter_md(tc)
    print(f"Team Charter created at {path}")


if __name__ == "__main__":
    verify()
