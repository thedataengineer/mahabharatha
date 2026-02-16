"""Verification script for Charter Enforcement."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add repo to path
sys.path.append(str(Path.cwd()))

from zerg.governance import CharterEnforcer, GovernanceService
from zerg.state.manager import StateManager


class TestEnforcement(unittest.TestCase):
    def setUp(self):
        # Create a dummy charter
        self.charter_path = Path("TEST_TEAM_CHARTER.md")
        self.charter_path.write_text(
            "# Team Charter\n\n## Core Principles\n- Write tests for everything\n- Document all APIs\n"
        )
        self.enforcer = CharterEnforcer(self.charter_path)

    def tearDown(self):
        if self.charter_path.exists():
            self.charter_path.unlink()

    def test_compliance(self):
        completion = "I implemented the feature, added unit tests, and created an artifact for documentation."
        compliant, reason = self.enforcer.audit_completion(completion)
        self.assertTrue(compliant)
        print(f"Compliance Check (Positive): {reason}")

    def test_violation(self):
        completion = "I implemented the feature. No tests were needed."
        compliant, reason = self.enforcer.audit_completion(completion)
        self.assertFalse(compliant)
        self.assertIn("Violation", reason)
        print(f"Violation Check (Negative): {reason}")

    def test_governance_audit(self):
        state = MagicMock(spec=StateManager)
        state.state_dir = Path("/tmp")
        gov = GovernanceService(state)
        gov.enforcer = self.enforcer  # Override with test enforcer

        summaries = {
            "task-001": "Feature done with tests and artifact docs.",
            "task-002": "Bug fixed but skipped tests.",
        }

        violations = gov.audit_level(summaries)
        self.assertNotIn("task-001", violations)
        self.assertIn("task-002", violations)
        print(f"Governance Level Audit: Found {len(violations)} violation(s).")


if __name__ == "__main__":
    unittest.main()
