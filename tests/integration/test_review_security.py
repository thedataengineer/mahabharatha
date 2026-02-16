"""Integration tests for review + security pipeline.

Tests the three-stage review workflow (Spec, Quality, Security) including:
- Full pipeline shows 3 stages
- --no-security flag skips Stage 3
- JSON output includes security data
- Files with secrets produce security findings
- overall_passed requires all 3 stages
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from zerg.commands.review import (
    CodeAnalyzer,
    ReviewCommand,
    ReviewResult,
)
from zerg.security import SecurityFinding, SecurityResult

# =============================================================================
# Test 1: Full pipeline shows 3 stages
# =============================================================================


class TestFullPipelineThreeStages:
    """Test that the full review pipeline invokes all 3 stages."""

    def test_full_mode_runs_all_three_stages(self, tmp_path: Path) -> None:
        """Full mode should produce results from Stage 1, 2, and 3."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")

        reviewer = ReviewCommand()
        result = reviewer.run([str(test_file)], mode="full")

        # Stage 1 (spec) and Stage 2 (quality) ran
        assert result.spec_passed is True
        assert result.quality_passed is True
        # Stage 3 (security) ran -- security_result should be populated
        assert result.security_result is not None
        assert isinstance(result.security_result, SecurityResult)

    def test_full_mode_text_output_mentions_all_stages(self, tmp_path: Path) -> None:
        """Text format output should reference Stage 1, Stage 2, Stage 3."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("x = 1\n")

        reviewer = ReviewCommand()
        result = reviewer.run([str(test_file)], mode="full")
        output = reviewer.format_result(result, fmt="text")

        assert "Stage 1" in output
        assert "Stage 2" in output
        assert "Stage 3" in output

    def test_full_mode_stage_details_populated(self, tmp_path: Path) -> None:
        """Stage 1 and Stage 2 should populate their details strings."""
        test_file = tmp_path / "example.py"
        test_file.write_text("def hello():\n    return 'world'\n")

        reviewer = ReviewCommand()
        result = reviewer.run([str(test_file)], mode="full")

        assert result.stage1_details != ""
        assert result.stage2_details != ""


# =============================================================================
# Test 2: --no-security skips Stage 3
# =============================================================================


class TestNoSecurityFlag:
    """Test that no_security=True skips Stage 3."""

    def test_no_security_skips_scan(self, tmp_path: Path) -> None:
        """With no_security=True, security_result should be None."""
        test_file = tmp_path / "module.py"
        test_file.write_text("x = 1\n")

        reviewer = ReviewCommand()
        result = reviewer.run([str(test_file)], mode="full", no_security=True)

        assert result.security_result is None

    def test_no_security_defaults_security_passed_true(self, tmp_path: Path) -> None:
        """When security is skipped, security_passed should default to True."""
        test_file = tmp_path / "module.py"
        test_file.write_text("x = 1\n")

        reviewer = ReviewCommand()
        result = reviewer.run([str(test_file)], mode="full", no_security=True)

        assert result.security_passed is True

    def test_no_security_text_output_shows_skipped(self, tmp_path: Path) -> None:
        """Text output should indicate security was SKIPPED."""
        test_file = tmp_path / "module.py"
        test_file.write_text("x = 1\n")

        reviewer = ReviewCommand()
        result = reviewer.run([str(test_file)], mode="full", no_security=True)
        output = reviewer.format_result(result, fmt="text")

        assert "SKIPPED" in output

    def test_no_security_does_not_call_security_review(self, tmp_path: Path) -> None:
        """Verify _run_security_review is NOT called when no_security=True."""
        test_file = tmp_path / "module.py"
        test_file.write_text("x = 1\n")

        reviewer = ReviewCommand()
        with patch.object(reviewer, "_run_security_review") as mock_security:
            reviewer.run([str(test_file)], mode="full", no_security=True)
            mock_security.assert_not_called()


# =============================================================================
# Test 3: JSON output includes security data
# =============================================================================


class TestJsonOutputSecurityData:
    """Test that JSON output includes security fields."""

    def test_json_includes_security_passed_key(self, tmp_path: Path) -> None:
        """JSON output must contain security_passed in the security section."""
        test_file = tmp_path / "app.py"
        test_file.write_text("x = 1\n")

        reviewer = ReviewCommand()
        result = reviewer.run([str(test_file)], mode="full")
        output = reviewer.format_result(result, fmt="json")
        parsed = json.loads(output)

        assert "security" in parsed
        assert "security_passed" in parsed["security"]

    def test_json_security_section_has_findings_array(self, tmp_path: Path) -> None:
        """JSON security section should have a findings array when scanned."""
        test_file = tmp_path / "app.py"
        test_file.write_text("x = 1\n")

        reviewer = ReviewCommand()
        result = reviewer.run([str(test_file)], mode="full")
        output = reviewer.format_result(result, fmt="json")
        parsed = json.loads(output)

        assert "findings" in parsed["security"]
        assert isinstance(parsed["security"]["findings"], list)

    def test_json_security_skipped_when_no_security(self, tmp_path: Path) -> None:
        """JSON should show skipped=True when --no-security is used."""
        test_file = tmp_path / "app.py"
        test_file.write_text("x = 1\n")

        reviewer = ReviewCommand()
        result = reviewer.run([str(test_file)], mode="full", no_security=True)
        output = reviewer.format_result(result, fmt="json")
        parsed = json.loads(output)

        assert parsed["security"]["skipped"] is True
        assert parsed["security"]["security_passed"] is True

    def test_json_includes_overall_passed(self, tmp_path: Path) -> None:
        """JSON output must include overall_passed field."""
        test_file = tmp_path / "app.py"
        test_file.write_text("x = 1\n")

        reviewer = ReviewCommand()
        result = reviewer.run([str(test_file)], mode="full")
        output = reviewer.format_result(result, fmt="json")
        parsed = json.loads(output)

        assert "overall_passed" in parsed

    def test_json_findings_have_expected_fields(self) -> None:
        """Each finding in JSON output should have category, severity, file, line, message, cwe."""
        finding = SecurityFinding(
            category="secret_detection",
            severity="high",
            file="config.py",
            line=10,
            message="Hardcoded secret",
            cwe="CWE-798",
            remediation="Use env vars",
            pattern_name="generic_password",
        )
        sec_result = SecurityResult(
            findings=[finding],
            categories_scanned=["secret_detection"],
            files_scanned=1,
            passed=False,
            summary={"high": 1},
        )
        result = ReviewResult(
            files_reviewed=1,
            items=[],
            spec_passed=True,
            quality_passed=True,
            security_passed=False,
            security_result=sec_result,
        )

        reviewer = ReviewCommand()
        output = reviewer.format_result(result, fmt="json")
        parsed = json.loads(output)

        assert len(parsed["security"]["findings"]) == 1
        f = parsed["security"]["findings"][0]
        assert f["category"] == "secret_detection"
        assert f["severity"] == "high"
        assert f["file"] == "config.py"
        assert f["line"] == 10
        assert f["message"] == "Hardcoded secret"
        assert f["cwe"] == "CWE-798"


# =============================================================================
# Test 4: Files with secrets produce security findings
# =============================================================================


class TestSecretsProduceFindings:
    """Test that files containing secrets produce security findings.

    Uses run_security_scan directly on isolated tmp directories to avoid
    scanning the project root (which has its own findings).
    """

    def test_file_with_api_key_pattern_produces_findings(self, tmp_path: Path) -> None:
        """A file with an AWS key pattern should produce a finding."""
        secret_file = tmp_path / "config.py"
        secret_file.write_text('AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n')

        from zerg.security import run_security_scan

        result = run_security_scan(path=str(tmp_path), categories=["secret_detection"], git_history_depth=0)
        secret_findings = [f for f in result.findings if f.category == "secret_detection"]
        assert len(secret_findings) >= 1

    def test_file_with_password_produces_findings(self, tmp_path: Path) -> None:
        """A file with a hardcoded password should produce a finding."""
        secret_file = tmp_path / "settings.py"
        secret_file.write_text('password = "supersecretpassword123"\n')

        from zerg.security import run_security_scan

        result = run_security_scan(path=str(tmp_path), categories=["secret_detection"], git_history_depth=0)
        secret_findings = [f for f in result.findings if f.category == "secret_detection"]
        assert len(secret_findings) >= 1

    def test_secrets_cause_security_passed_false(self, tmp_path: Path) -> None:
        """Critical/high findings should cause passed=False on SecurityResult."""
        secret_file = tmp_path / "leak.py"
        # Use a pattern that triggers critical severity (AWS key)
        secret_file.write_text('key = "AKIAIOSFODNN7EXAMPLE"\n')

        from zerg.security import run_security_scan

        result = run_security_scan(path=str(tmp_path), categories=["secret_detection"], git_history_depth=0)
        critical_or_high = [
            f for f in result.findings if f.severity in ("critical", "high") and f.category == "secret_detection"
        ]
        if critical_or_high:
            assert result.passed is False

    def test_clean_file_has_no_secret_findings(self, tmp_path: Path) -> None:
        """A clean file should produce no secret_detection findings."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text("def add(a, b):\n    return a + b\n")

        from zerg.security import run_security_scan

        result = run_security_scan(path=str(tmp_path), categories=["secret_detection"], git_history_depth=0)
        secret_findings = [f for f in result.findings if f.category == "secret_detection"]
        assert len(secret_findings) == 0


# =============================================================================
# Test 5: overall_passed requires all 3 stages
# =============================================================================


class TestOverallPassedRequiresAllStages:
    """Test that overall_passed is the AND of all three stages."""

    def test_all_pass_means_overall_pass(self) -> None:
        """spec=True, quality=True, security=True -> overall_passed=True."""
        result = ReviewResult(
            files_reviewed=1,
            items=[],
            spec_passed=True,
            quality_passed=True,
            security_passed=True,
        )
        assert result.overall_passed is True

    def test_security_fail_means_overall_fail(self) -> None:
        """spec=True, quality=True, security=False -> overall_passed=False."""
        result = ReviewResult(
            files_reviewed=1,
            items=[],
            spec_passed=True,
            quality_passed=True,
            security_passed=False,
        )
        assert result.overall_passed is False

    def test_spec_fail_means_overall_fail(self) -> None:
        """spec=False, quality=True, security=True -> overall_passed=False."""
        result = ReviewResult(
            files_reviewed=1,
            items=[],
            spec_passed=False,
            quality_passed=True,
            security_passed=True,
        )
        assert result.overall_passed is False

    def test_quality_fail_means_overall_fail(self) -> None:
        """spec=True, quality=False, security=True -> overall_passed=False."""
        result = ReviewResult(
            files_reviewed=1,
            items=[],
            spec_passed=True,
            quality_passed=False,
            security_passed=True,
        )
        assert result.overall_passed is False

    def test_all_fail_means_overall_fail(self) -> None:
        """All three stages failing -> overall_passed=False."""
        result = ReviewResult(
            files_reviewed=1,
            items=[],
            spec_passed=False,
            quality_passed=False,
            security_passed=False,
        )
        assert result.overall_passed is False

    @pytest.mark.parametrize(
        "spec,quality,security,expected",
        [
            (True, True, True, True),
            (True, True, False, False),
            (True, False, True, False),
            (False, True, True, False),
            (True, False, False, False),
            (False, True, False, False),
            (False, False, True, False),
            (False, False, False, False),
        ],
        ids=[
            "all-pass",
            "security-fail",
            "quality-fail",
            "spec-fail",
            "quality+security-fail",
            "spec+security-fail",
            "spec+quality-fail",
            "all-fail",
        ],
    )
    def test_overall_passed_truth_table(self, spec: bool, quality: bool, security: bool, expected: bool) -> None:
        """Exhaustive truth table for overall_passed."""
        result = ReviewResult(
            files_reviewed=1,
            items=[],
            spec_passed=spec,
            quality_passed=quality,
            security_passed=security,
        )
        assert result.overall_passed is expected


# =============================================================================
# CodeAnalyzer: Verify no hardcoded_secret pattern
# =============================================================================


class TestCodeAnalyzerNoHardcodedSecret:
    """Verify CodeAnalyzer no longer has the hardcoded_secret pattern."""

    def test_no_hardcoded_secret_in_patterns(self) -> None:
        """CodeAnalyzer.PATTERNS should not contain 'hardcoded_secret'.

        Secret detection is now handled by the security package (Stage 3),
        not by the code analyzer (Stage 2).
        """
        analyzer = CodeAnalyzer()
        assert "hardcoded_secret" not in analyzer.PATTERNS
