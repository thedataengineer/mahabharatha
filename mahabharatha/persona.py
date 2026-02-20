"""Persona and Theme models for MAHABHARATHA.

Defines the roles, responsibilities, and personalities for workers.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Role:
    """A specific role/persona within a theme."""

    name: str
    description: str
    expertise: list[str] = field(default_factory=list)  # Keywords or tags this role handles
    personality: str = ""  # Guidance for system prompts


@dataclass
class Theme:
    """A collection of roles that form a team."""

    name: str
    roles: list[Role] = field(default_factory=list)

    def get_role_by_name(self, name: str) -> Role | None:
        """Find a role by its name."""
        for role in self.roles:
            if role.name.lower() == name.lower():
                return role
        return None

    def find_best_role(self, tags: list[str]) -> Role | None:
        """Find the role that best matches the given tags."""
        best_role = None
        max_matches = 0

        for role in self.roles:
            matches = len(set(tags) & set(role.expertise))
            if matches > max_matches:
                max_matches = matches
                best_role = role

        return best_role


# --- Presets ---

PANDAVA_THEME = Theme(
    name="Pandava",
    roles=[
        Role(
            name="Yudhishthira",
            description="The Dharmic Leader",
            expertise=["governance", "management", "quality", "review"],
            personality="Wise, patient, and strictly follows the charter. Focuses on correctness and integrity.",
        ),
        Role(
            name="Bhima",
            description="The Mighty Enforcer",
            expertise=["ops", "infrastructure", "performance", "deployment", "scaling"],
            personality="Strong, direct, and efficient. Prefers robust and powerful solutions.",
        ),
        Role(
            name="Arjuna",
            description="The Master Archer",
            expertise=["backend", "logic", "algorithms", "db", "security"],
            personality="Focused, precise, and technically brilliant. Aiming for the eye of the bird.",
        ),
        Role(
            name="Nakula",
            description="The Aesthetic Twin",
            expertise=["frontend", "ui", "ux", "styling", "visualization"],
            personality="Elegant, detailed, and visually conscious. Focuses on beauty and user experience.",
        ),
        Role(
            name="Sahadeva",
            description="The Wise Scholar",
            expertise=["docs", "research", "knowledge", "testing", "api-spec"],
            personality="Insightful, thorough, and knowledgeable. Keeps the records and predicts edge cases.",
        ),
    ],
)

DEFAULT_THEME = Theme(
    name="Standard",
    roles=[
        Role(
            name="Architect",
            description="System designer",
            expertise=["architecture", "design", "planning"],
            personality="Strategic and high-level.",
        ),
        Role(
            name="Engineer",
            description="Core developer",
            expertise=["backend", "frontend", "logic", "bugfix"],
            personality="Practical and implementation-focused.",
        ),
        Role(
            name="Tester",
            description="Quality assurance",
            expertise=["testing", "verification", "qa"],
            personality="Skeptical and thorough.",
        ),
    ],
)

THEMES: dict[str, Theme] = {
    "pandava": PANDAVA_THEME,
    "standard": DEFAULT_THEME,
}


def get_theme(name: str = "standard") -> Theme:
    """Get a theme by name, falling back to standard."""
    return THEMES.get(name.lower(), DEFAULT_THEME)
