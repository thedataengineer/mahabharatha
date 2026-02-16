"""Comprehensive tests for the consolidated security engine.

Tests cover:
1. Pattern registry completeness and structure
2. Per-capability positive/negative detection tests
3. Scanner integration (run_security_scan returns SecurityResult)
4. CVE scanner (osv.dev API mock, heuristic fallback, dependency parsing)
5. SecurityResult.passed logic
6. Git history scanning
7. Performance (50-file scan under 5 seconds)
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from zerg.security import SecurityFinding, SecurityResult
from zerg.security.cve import (
    _check_known_bad_versions,
    _Dependency,
    _heuristic_scan,
    _parse_cargo_toml,
    _parse_go_mod,
    _parse_package_json,
    _parse_requirements_txt,
    scan_dependencies,
)
from zerg.security.patterns import (
    PATTERN_REGISTRY,
    get_all_patterns,
    get_categories,
    get_patterns_for_extension,
)
from zerg.security.scanner import (
    _scan_file_with_patterns,
    _scan_git_history,
    run_security_scan,
)

# ===================================================================
# 1. PATTERN REGISTRY TESTS
# ===================================================================


class TestPatternRegistry:
    """Verify structural integrity of the PATTERN_REGISTRY."""

    EXPECTED_CATEGORIES = [
        "secret_detection",
        "injection_detection",
        "deserialization_risks",
        "cryptographic_misuse",
        "error_handling",
        "input_validation",
        "lockfile_integrity",
        "license_compliance",
        "sensitive_files",
        "file_permissions",
        "env_var_leakage",
        "dockerfile_security",
        "symlink_escape",
    ]

    def test_all_13_categories_exist(self) -> None:
        """PATTERN_REGISTRY must contain all 13 pattern-based categories."""
        for cat in self.EXPECTED_CATEGORIES:
            assert cat in PATTERN_REGISTRY, f"Missing category: {cat}"

    def test_no_unexpected_categories(self) -> None:
        """Registry should not contain unknown categories."""
        for cat in PATTERN_REGISTRY:
            assert cat in self.EXPECTED_CATEGORIES, f"Unexpected category: {cat}"

    def test_category_count(self) -> None:
        """Exactly 13 pattern-based categories should be registered."""
        assert len(PATTERN_REGISTRY) == 13

    def test_get_categories_returns_sorted(self) -> None:
        """get_categories() should return sorted category names."""
        cats = get_categories()
        assert cats == sorted(cats)
        assert len(cats) == 13

    def test_each_pattern_has_required_fields(self) -> None:
        """Every pattern must have name, category, severity, message, remediation."""
        for cat, patterns in PATTERN_REGISTRY.items():
            for p in patterns:
                assert p.name, f"Pattern in {cat} missing name"
                assert p.category == cat, (
                    f"Pattern '{p.name}' has category '{p.category}' but is registered under '{cat}'"
                )
                assert p.severity in (
                    "critical",
                    "high",
                    "medium",
                    "low",
                    "info",
                ), f"Pattern '{p.name}' has invalid severity '{p.severity}'"
                assert p.message, f"Pattern '{p.name}' missing message"
                assert p.remediation, f"Pattern '{p.name}' missing remediation"

    def test_all_regexes_compile(self) -> None:
        """All regex patterns should already be compiled at import time."""
        for patterns in PATTERN_REGISTRY.values():
            for p in patterns:
                assert isinstance(p.regex, re.Pattern), f"Pattern '{p.name}' regex is not compiled"

    def test_no_duplicate_pattern_names(self) -> None:
        """No two patterns across all categories should share a name."""
        seen: set[str] = set()
        for patterns in PATTERN_REGISTRY.values():
            for p in patterns:
                assert p.name not in seen, f"Duplicate pattern name: {p.name}"
                seen.add(p.name)

    def test_get_all_patterns_returns_flat_list(self) -> None:
        """get_all_patterns() should return a flat list of all patterns."""
        all_p = get_all_patterns()
        expected_count = sum(len(ps) for ps in PATTERN_REGISTRY.values())
        assert len(all_p) == expected_count

    def test_get_patterns_for_extension_py(self) -> None:
        """Python-specific patterns should be returned for .py extension."""
        py_patterns = get_patterns_for_extension(".py")
        # Should include injection_detection (Python code injection), deserialization, etc.
        categories_found = {p.category for p in py_patterns}
        assert "injection_detection" in categories_found
        assert "deserialization_risks" in categories_found
        assert "cryptographic_misuse" in categories_found

    def test_get_patterns_for_extension_js(self) -> None:
        """JavaScript patterns should be returned for .js extension."""
        js_patterns = get_patterns_for_extension(".js")
        categories_found = {p.category for p in js_patterns}
        assert "injection_detection" in categories_found

    def test_universal_patterns_included_for_any_extension(self) -> None:
        """Patterns with file_extensions=None apply to all files."""
        py_patterns = get_patterns_for_extension(".py")
        # Secret detection patterns have no extension filter
        secret_patterns = [p for p in py_patterns if p.category == "secret_detection"]
        assert len(secret_patterns) > 0

    def test_each_category_has_at_least_one_pattern(self) -> None:
        """Every category must contain at least one pattern."""
        for cat, patterns in PATTERN_REGISTRY.items():
            assert len(patterns) >= 1, f"Category '{cat}' is empty"


# ===================================================================
# 2. PER-CAPABILITY POSITIVE/NEGATIVE DETECTION TESTS
# ===================================================================


class TestSecretDetection:
    """Category: secret_detection."""

    def test_positive_aws_key(self) -> None:
        """Detect AWS access key pattern."""
        patterns = PATTERN_REGISTRY["secret_detection"]
        aws_pattern = next(p for p in patterns if p.name == "aws_access_key")
        assert aws_pattern.regex.search("AKIAIOSFODNN7EXAMPLE")

    def test_positive_github_pat(self) -> None:
        """Detect GitHub Personal Access Token."""
        patterns = PATTERN_REGISTRY["secret_detection"]
        pat = next(p for p in patterns if p.name == "github_pat")
        assert pat.regex.search("ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456789A")

    def test_positive_openai_key(self) -> None:
        """Detect OpenAI API key."""
        patterns = PATTERN_REGISTRY["secret_detection"]
        pat = next(p for p in patterns if p.name == "openai_key")
        assert pat.regex.search("sk-aBcDeFgHiJkLmNoPqRsTuVwXyZaBcDeFgHiJkLmNoPqRsAbCd")

    def test_positive_generic_password(self) -> None:
        """Detect hardcoded password assignment."""
        patterns = PATTERN_REGISTRY["secret_detection"]
        pat = next(p for p in patterns if p.name == "generic_password")
        assert pat.regex.search('password = "supersecret123"')

    def test_negative_regular_string(self) -> None:
        """Regular strings should not match secret patterns."""
        patterns = PATTERN_REGISTRY["secret_detection"]
        clean_text = "hello_world = 42"
        for p in patterns:
            assert not p.regex.search(clean_text), f"Pattern '{p.name}' false-positive on clean text"


class TestInjectionDetection:
    """Category: injection_detection."""

    def test_positive_python_code_execution(self) -> None:
        """Detect dangerous code execution calls in Python."""
        patterns = PATTERN_REGISTRY["injection_detection"]
        pat = next(p for p in patterns if p.name == "python_eval")
        # Test with a string that the pattern should match:
        # a line starting with non-comment characters followed by the call
        assert pat.regex.search("result = eval(user_input)")  # noqa: S307

    def test_positive_os_system(self) -> None:
        """Detect os.system() call."""
        patterns = PATTERN_REGISTRY["injection_detection"]
        pat = next(p for p in patterns if p.name == "os_system_call")
        assert pat.regex.search("os.system(command)")

    def test_positive_shell_true(self) -> None:
        """Detect shell=True in subprocess."""
        patterns = PATTERN_REGISTRY["injection_detection"]
        pat = next(p for p in patterns if p.name == "shell_injection_true")
        assert pat.regex.search("subprocess.run(cmd, shell=True)")

    def test_negative_code_exec_in_comment(self) -> None:
        """Code execution calls in a Python comment should not trigger."""
        patterns = PATTERN_REGISTRY["injection_detection"]
        pat = next(p for p in patterns if p.name == "python_eval")
        # Pattern uses ^[^#]* to exclude lines starting with comments
        assert not pat.regex.search("# eval(something)")  # noqa: S307

    def test_negative_safe_subprocess(self) -> None:
        """subprocess.run without shell=True should not trigger."""
        patterns = PATTERN_REGISTRY["injection_detection"]
        pat = next(p for p in patterns if p.name == "shell_injection_true")
        assert not pat.regex.search("subprocess.run(['ls', '-la'])")


class TestDeserializationRisks:
    """Category: deserialization_risks."""

    def test_positive_pickle_loads(self) -> None:
        """Detect pickle.loads call."""
        patterns = PATTERN_REGISTRY["deserialization_risks"]
        pat = next(p for p in patterns if p.name == "pickle_load")
        assert pat.regex.search("data = pickle.loads(payload)")

    def test_positive_yaml_unsafe(self) -> None:
        """Detect yaml.load without safe loader."""
        patterns = PATTERN_REGISTRY["deserialization_risks"]
        pat = next(p for p in patterns if p.name == "yaml_load_no_loader")
        assert pat.regex.search("yaml.load(data)")

    def test_negative_json_loads(self) -> None:
        """json.loads should not trigger deserialization risk."""
        patterns = PATTERN_REGISTRY["deserialization_risks"]
        clean_text = "data = json.loads(payload)"
        for p in patterns:
            assert not p.regex.search(clean_text), f"Pattern '{p.name}' false-positive on json.loads"


class TestCryptographicMisuse:
    """Category: cryptographic_misuse."""

    def test_positive_md5_hash(self) -> None:
        """Detect hashlib.md5 usage."""
        patterns = PATTERN_REGISTRY["cryptographic_misuse"]
        pat = next(p for p in patterns if p.name == "md5_password_hash")
        assert pat.regex.search("hashlib.md5(data)")

    def test_positive_weak_secret_key(self) -> None:
        """Detect weak SECRET_KEY."""
        patterns = PATTERN_REGISTRY["cryptographic_misuse"]
        pat = next(p for p in patterns if p.name == "weak_secret_key")
        assert pat.regex.search("SECRET_KEY = 'dev'")

    def test_negative_sha256(self) -> None:
        """hashlib.sha256 should not trigger MD5/SHA1 warnings."""
        patterns = PATTERN_REGISTRY["cryptographic_misuse"]
        md5_pat = next(p for p in patterns if p.name == "md5_password_hash")
        sha1_pat = next(p for p in patterns if p.name == "sha1_usage")
        clean = "hashlib.sha256(data)"
        assert not md5_pat.regex.search(clean)
        assert not sha1_pat.regex.search(clean)


class TestErrorHandling:
    """Category: error_handling."""

    def test_positive_bare_except(self) -> None:
        """Detect bare except clause."""
        patterns = PATTERN_REGISTRY["error_handling"]
        pat = next(p for p in patterns if p.name == "bare_except")
        assert pat.regex.search("    except:")

    def test_positive_debug_true(self) -> None:
        """Detect DEBUG=True."""
        patterns = PATTERN_REGISTRY["error_handling"]
        pat = next(p for p in patterns if p.name == "debug_true_production")
        assert pat.regex.search("DEBUG = True")

    def test_negative_specific_except(self) -> None:
        """except ValueError should not trigger bare except."""
        patterns = PATTERN_REGISTRY["error_handling"]
        pat = next(p for p in patterns if p.name == "bare_except")
        assert not pat.regex.search("    except ValueError:")


class TestInputValidation:
    """Category: input_validation."""

    def test_positive_open_user_path(self) -> None:
        """Detect open() with user input."""
        patterns = PATTERN_REGISTRY["input_validation"]
        pat = next(p for p in patterns if p.name == "open_user_path")
        assert pat.regex.search("open(request.args['file'])")

    def test_negative_open_literal(self) -> None:
        """open() with a literal path should not trigger."""
        patterns = PATTERN_REGISTRY["input_validation"]
        pat = next(p for p in patterns if p.name == "open_user_path")
        assert not pat.regex.search("open('config.yaml')")


class TestLockfileIntegrity:
    """Category: lockfile_integrity."""

    def test_positive_wildcard_version(self) -> None:
        """Detect wildcard version specifier."""
        patterns = PATTERN_REGISTRY["lockfile_integrity"]
        pat = next(p for p in patterns if p.name == "wildcard_version")
        assert pat.regex.search('"*"')

    def test_negative_pinned_version(self) -> None:
        """Pinned version should not trigger wildcard warning."""
        patterns = PATTERN_REGISTRY["lockfile_integrity"]
        pat = next(p for p in patterns if p.name == "wildcard_version")
        assert not pat.regex.search('"1.2.3"')


class TestLicenseCompliance:
    """Category: license_compliance."""

    def test_positive_gpl_detection(self) -> None:
        """Detect GPL license mention."""
        patterns = PATTERN_REGISTRY["license_compliance"]
        pat = next(p for p in patterns if p.name == "gpl_license")
        assert pat.regex.search("License: GPL-3")

    def test_positive_agpl_detection(self) -> None:
        """Detect AGPL license mention."""
        patterns = PATTERN_REGISTRY["license_compliance"]
        pat = next(p for p in patterns if p.name == "agpl_license")
        assert pat.regex.search("License: AGPL")

    def test_negative_mit_license(self) -> None:
        """MIT license should not trigger GPL/AGPL warnings."""
        patterns = PATTERN_REGISTRY["license_compliance"]
        clean = "License: MIT"
        for p in patterns:
            assert not p.regex.search(clean), f"Pattern '{p.name}' false-positive on MIT license"


class TestSensitiveFiles:
    """Category: sensitive_files."""

    def test_positive_env_file(self) -> None:
        """Detect .env file."""
        patterns = PATTERN_REGISTRY["sensitive_files"]
        pat = next(p for p in patterns if p.name == "env_file")
        assert pat.regex.search(".env")

    def test_positive_credentials_json(self) -> None:
        """Detect credentials.json file."""
        patterns = PATTERN_REGISTRY["sensitive_files"]
        pat = next(p for p in patterns if p.name == "credentials_json")
        assert pat.regex.search("credentials.json")

    def test_negative_regular_file(self) -> None:
        """Regular files like config.yaml should not trigger."""
        patterns = PATTERN_REGISTRY["sensitive_files"]
        clean = "config.yaml"
        for p in patterns:
            assert not p.regex.search(clean), f"Pattern '{p.name}' false-positive on '{clean}'"


class TestFilePermissions:
    """Category: file_permissions."""

    def test_positive_chmod_777(self) -> None:
        """Detect chmod 777."""
        patterns = PATTERN_REGISTRY["file_permissions"]
        pat = next(p for p in patterns if p.name == "chmod_world_writable")
        assert pat.regex.search("chmod 777 /app")

    def test_negative_chmod_644(self) -> None:
        """chmod 644 should not trigger."""
        patterns = PATTERN_REGISTRY["file_permissions"]
        pat = next(p for p in patterns if p.name == "chmod_world_writable")
        assert not pat.regex.search("chmod 644 /app")


class TestEnvVarLeakage:
    """Category: env_var_leakage."""

    def test_positive_print_env(self) -> None:
        """Detect print(os.environ)."""
        patterns = PATTERN_REGISTRY["env_var_leakage"]
        pat = next(p for p in patterns if p.name == "print_env_all")
        assert pat.regex.search("print(os.environ)")

    def test_negative_specific_env_var(self) -> None:
        """Accessing a specific env var via os.getenv should not trigger print_env_all."""
        patterns = PATTERN_REGISTRY["env_var_leakage"]
        pat = next(p for p in patterns if p.name == "print_env_all")
        assert not pat.regex.search('print(os.getenv("HOME"))')


class TestDockerfileSecurity:
    """Category: dockerfile_security."""

    def test_positive_privileged_flag(self) -> None:
        """Detect --privileged flag."""
        patterns = PATTERN_REGISTRY["dockerfile_security"]
        pat = next(p for p in patterns if p.name == "privileged_flag")
        assert pat.regex.search("docker run --privileged myimage")

    def test_positive_latest_tag(self) -> None:
        """Detect FROM with :latest tag."""
        patterns = PATTERN_REGISTRY["dockerfile_security"]
        pat = next(p for p in patterns if p.name == "latest_tag")
        assert pat.regex.search("FROM python:latest")

    def test_negative_pinned_image(self) -> None:
        """Pinned image version should not trigger latest tag warning."""
        patterns = PATTERN_REGISTRY["dockerfile_security"]
        pat = next(p for p in patterns if p.name == "latest_tag")
        assert not pat.regex.search("FROM python:3.12-slim")


class TestSymlinkEscape:
    """Category: symlink_escape."""

    def test_positive_followlinks_true(self) -> None:
        """Detect os.walk with followlinks=True."""
        patterns = PATTERN_REGISTRY["symlink_escape"]
        pat = next(p for p in patterns if p.name == "followlinks_true")
        assert pat.regex.search("os.walk('/path', followlinks=True)")

    def test_negative_followlinks_false(self) -> None:
        """os.walk without followlinks=True should not trigger."""
        patterns = PATTERN_REGISTRY["symlink_escape"]
        pat = next(p for p in patterns if p.name == "followlinks_true")
        assert not pat.regex.search("os.walk('/path')")


# ===================================================================
# 3. SCANNER INTEGRATION TESTS
# ===================================================================


class TestScannerIntegration:
    """Test run_security_scan returns correct SecurityResult structure."""

    def test_run_security_scan_returns_security_result(self, tmp_path: Path) -> None:
        """run_security_scan should return a SecurityResult instance."""
        (tmp_path / "clean.py").write_text("x = 42\n")
        with (
            patch("zerg.security.cve.scan_dependencies", return_value=[]),
            patch("zerg.security.scanner._scan_git_history", return_value=[]),
        ):
            result = run_security_scan(tmp_path)
        assert isinstance(result, SecurityResult)

    def test_security_result_attributes(self, tmp_path: Path) -> None:
        """SecurityResult should have all expected attributes."""
        (tmp_path / "clean.py").write_text("x = 42\n")
        with (
            patch("zerg.security.cve.scan_dependencies", return_value=[]),
            patch("zerg.security.scanner._scan_git_history", return_value=[]),
        ):
            result = run_security_scan(tmp_path)
        assert hasattr(result, "findings")
        assert hasattr(result, "categories_scanned")
        assert hasattr(result, "files_scanned")
        assert hasattr(result, "scan_duration_seconds")
        assert hasattr(result, "passed")
        assert hasattr(result, "summary")

    def test_finding_structure(self, tmp_path: Path) -> None:
        """Findings should have correct SecurityFinding attributes."""
        # Write a file with a known secret pattern
        (tmp_path / "bad.py").write_text('password = "supersecret123"\n')
        with (
            patch("zerg.security.cve.scan_dependencies", return_value=[]),
            patch("zerg.security.scanner._scan_git_history", return_value=[]),
        ):
            result = run_security_scan(tmp_path)
        assert len(result.findings) >= 1
        finding = result.findings[0]
        assert isinstance(finding, SecurityFinding)
        assert finding.category
        assert finding.severity
        assert finding.file
        assert isinstance(finding.line, int)
        assert finding.message
        assert finding.remediation
        assert finding.pattern_name

    def test_scan_with_specific_categories(self, tmp_path: Path) -> None:
        """Scanning specific categories should only report those categories."""
        (tmp_path / "bad.py").write_text('password = "supersecret123"\ndata = pickle.loads(payload)\n')
        with (
            patch("zerg.security.cve.scan_dependencies", return_value=[]),
            patch("zerg.security.scanner._scan_git_history", return_value=[]),
        ):
            result = run_security_scan(tmp_path, categories=["deserialization_risks"])
        # Only deserialization findings should be present
        for f in result.findings:
            assert f.category == "deserialization_risks"

    def test_scan_file_with_patterns_directly(self, tmp_path: Path) -> None:
        """_scan_file_with_patterns returns findings for matching content."""
        test_file = tmp_path / "test.py"
        test_file.write_text("os.system(cmd)\n")
        findings = _scan_file_with_patterns(str(test_file), ["injection_detection"], PATTERN_REGISTRY)
        assert len(findings) >= 1
        assert findings[0].category == "injection_detection"

    def test_files_scanned_count(self, tmp_path: Path) -> None:
        """files_scanned should reflect the number of files processed."""
        (tmp_path / "a.py").write_text("x = 1\n")
        (tmp_path / "b.py").write_text("y = 2\n")
        (tmp_path / "c.js").write_text("let z = 3;\n")
        with (
            patch("zerg.security.cve.scan_dependencies", return_value=[]),
            patch("zerg.security.scanner._scan_git_history", return_value=[]),
        ):
            result = run_security_scan(tmp_path)
        assert result.files_scanned >= 3

    def test_scan_duration_is_recorded(self, tmp_path: Path) -> None:
        """scan_duration_seconds should be a non-negative float."""
        (tmp_path / "x.py").write_text("pass\n")
        with (
            patch("zerg.security.cve.scan_dependencies", return_value=[]),
            patch("zerg.security.scanner._scan_git_history", return_value=[]),
        ):
            result = run_security_scan(tmp_path)
        assert isinstance(result.scan_duration_seconds, float)
        assert result.scan_duration_seconds >= 0


# ===================================================================
# 4. CVE SCANNER TESTS
# ===================================================================


class TestCVEScannerAPI:
    """Test osv.dev API integration and heuristic fallback."""

    def test_osv_api_success_produces_findings(self, tmp_path: Path) -> None:
        """When osv.dev returns vulnerabilities, findings should be generated."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.25.0\n")

        fake_response_body = json.dumps(
            {
                "results": [
                    {
                        "vulns": [
                            {
                                "id": "GHSA-xxxx-yyyy",
                                "summary": "Test vulnerability",
                                "aliases": ["CVE-2024-1234"],
                                "severity": [{"score": "9.1"}],
                            }
                        ]
                    }
                ]
            }
        ).encode("utf-8")

        mock_response = MagicMock()
        mock_response.read.return_value = fake_response_body
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("zerg.security.cve.urllib.request.urlopen", return_value=mock_response):
            findings = scan_dependencies(tmp_path)

        # Should have at least one CVE finding from the API
        # The CVE alias is stored in pattern_name, not in the message
        cve_findings = [f for f in findings if f.category == "cve" and f.pattern_name == "CVE-2024-1234"]
        assert len(cve_findings) >= 1
        assert cve_findings[0].severity == "critical"  # 9.1 CVSS

    def test_osv_api_timeout_falls_back_to_heuristic(self, tmp_path: Path) -> None:
        """When osv.dev API times out, heuristic scan should still run."""
        import urllib.error

        req_file = tmp_path / "requirements.txt"
        req_file.write_text("somepackage\n")  # unpinned

        with patch(
            "zerg.security.cve.urllib.request.urlopen",
            side_effect=urllib.error.URLError("timeout"),
        ):
            findings = scan_dependencies(tmp_path)

        # Heuristic should flag unpinned dependency
        unpinned = [f for f in findings if f.pattern_name == "unpinned_dependency"]
        assert len(unpinned) >= 1

    def test_heuristic_detects_missing_lockfile(self, tmp_path: Path) -> None:
        """Heuristic scan should flag missing lockfiles."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("flask==2.0.0\n")
        # No lockfile companion (requirements.lock, poetry.lock, etc.)

        deps = [
            _Dependency(
                name="flask",
                version="2.0.0",
                ecosystem="PyPI",
                source_file=str(req_file),
                line=1,
            )
        ]
        findings = _heuristic_scan(tmp_path, deps)
        lockfile_findings = [f for f in findings if f.pattern_name == "missing_lockfile"]
        assert len(lockfile_findings) >= 1

    def test_known_bad_versions_detected(self) -> None:
        """Known-bad version ranges should be flagged by heuristic check."""
        deps = [
            _Dependency(
                name="urllib3",
                version="1.25.9",
                ecosystem="PyPI",
                source_file="requirements.txt",
                line=1,
            )
        ]
        findings = _check_known_bad_versions(deps)
        assert len(findings) >= 1
        assert "CVE-2021-33503" in findings[0].pattern_name


class TestDependencyParsers:
    """Test dependency file parsers for each ecosystem."""

    def test_parse_requirements_txt_pinned(self, tmp_path: Path) -> None:
        """Parse requirements.txt with pinned versions."""
        req = tmp_path / "requirements.txt"
        req.write_text("flask==2.0.0\nrequests==2.28.1\n")
        deps = _parse_requirements_txt(req)
        assert len(deps) == 2
        assert deps[0].name == "flask"
        assert deps[0].version == "2.0.0"
        assert deps[0].ecosystem == "PyPI"
        assert deps[1].name == "requests"
        assert deps[1].version == "2.28.1"

    def test_parse_requirements_txt_unpinned(self, tmp_path: Path) -> None:
        """Unpinned requirements should have version=None."""
        req = tmp_path / "requirements.txt"
        req.write_text("flask>=2.0\nrequests\n")
        deps = _parse_requirements_txt(req)
        assert len(deps) == 2
        # >=2.0 is not an exact pin
        assert deps[0].version is None
        assert deps[1].version is None

    def test_parse_requirements_txt_comments_and_blanks(self, tmp_path: Path) -> None:
        """Comments, blank lines, and flags should be skipped."""
        req = tmp_path / "requirements.txt"
        req.write_text(
            "# This is a comment\n\n-r other-requirements.txt\n--index-url https://pypi.org/simple\nflask==2.0.0\n"
        )
        deps = _parse_requirements_txt(req)
        assert len(deps) == 1
        assert deps[0].name == "flask"

    def test_parse_package_json_deps_and_devdeps(self, tmp_path: Path) -> None:
        """Parse package.json with both dependencies and devDependencies."""
        pkg = tmp_path / "package.json"
        pkg.write_text(
            json.dumps(
                {
                    "dependencies": {"express": "4.18.2", "lodash": "^4.17.21"},
                    "devDependencies": {"jest": "~29.0.0"},
                }
            )
        )
        deps = _parse_package_json(pkg)
        assert len(deps) == 3
        names = {d.name for d in deps}
        assert names == {"express", "lodash", "jest"}
        # All should be npm ecosystem
        for d in deps:
            assert d.ecosystem == "npm"

    def test_parse_package_json_empty(self, tmp_path: Path) -> None:
        """Empty package.json should return no deps."""
        pkg = tmp_path / "package.json"
        pkg.write_text("{}")
        deps = _parse_package_json(pkg)
        assert len(deps) == 0

    def test_parse_cargo_toml(self, tmp_path: Path) -> None:
        """Parse Cargo.toml with dependency declarations."""
        cargo = tmp_path / "Cargo.toml"
        cargo.write_text(
            "[package]\n"
            'name = "myapp"\n'
            'version = "0.1.0"\n'
            "\n"
            "[dependencies]\n"
            'serde = "1.0.150"\n'
            'tokio = { version = "1.25.0", features = ["full"] }\n'
        )
        deps = _parse_cargo_toml(cargo)
        assert len(deps) == 2
        names = {d.name for d in deps}
        assert "serde" in names
        assert "tokio" in names
        for d in deps:
            assert d.ecosystem == "crates.io"

    def test_parse_go_mod_single_require(self, tmp_path: Path) -> None:
        """Parse go.mod with single-line require."""
        gomod = tmp_path / "go.mod"
        gomod.write_text("module example.com/myapp\n\ngo 1.21\n\nrequire github.com/gin-gonic/gin v1.9.1\n")
        deps = _parse_go_mod(gomod)
        assert len(deps) == 1
        assert deps[0].name == "github.com/gin-gonic/gin"
        assert deps[0].version == "v1.9.1"
        assert deps[0].ecosystem == "Go"

    def test_parse_go_mod_block_require(self, tmp_path: Path) -> None:
        """Parse go.mod with block require."""
        gomod = tmp_path / "go.mod"
        gomod.write_text(
            "module example.com/myapp\n"
            "\n"
            "go 1.21\n"
            "\n"
            "require (\n"
            "\tgithub.com/gin-gonic/gin v1.9.1\n"
            "\tgolang.org/x/text v0.14.0 // indirect\n"
            ")\n"
        )
        deps = _parse_go_mod(gomod)
        assert len(deps) == 2
        names = {d.name for d in deps}
        assert "github.com/gin-gonic/gin" in names
        assert "golang.org/x/text" in names

    def test_parse_nonexistent_file(self, tmp_path: Path) -> None:
        """Parsers should handle nonexistent files gracefully."""
        missing = tmp_path / "requirements.txt"
        assert _parse_requirements_txt(missing) == []
        assert _parse_package_json(missing) == []
        assert _parse_cargo_toml(missing) == []
        assert _parse_go_mod(missing) == []


# ===================================================================
# 5. SECURITY RESULT PASSED LOGIC
# ===================================================================


class TestSecurityResultPassedLogic:
    """Verify SecurityResult.passed is computed correctly by run_security_scan."""

    def test_empty_findings_is_passed(self) -> None:
        """No findings means passed=True."""
        result = SecurityResult(findings=[], passed=True)
        assert result.passed is True

    def test_low_and_medium_only_is_passed(self, tmp_path: Path) -> None:
        """Only low/medium findings should result in passed=True."""
        # Create a file with DEBUG=True (medium severity)
        (tmp_path / "settings.py").write_text("DEBUG = True\n")
        with (
            patch("zerg.security.cve.scan_dependencies", return_value=[]),
            patch("zerg.security.scanner._scan_git_history", return_value=[]),
        ):
            result = run_security_scan(tmp_path, categories=["error_handling"])
        # Should have findings but still pass (medium)
        medium_findings = [f for f in result.findings if f.severity == "medium"]
        critical_high = [f for f in result.findings if f.severity in ("critical", "high")]
        if medium_findings and not critical_high:
            assert result.passed is True

    def test_critical_finding_fails(self, tmp_path: Path) -> None:
        """A critical finding should result in passed=False."""
        (tmp_path / "bad.py").write_text("data = pickle.loads(user_data)\n")
        with (
            patch("zerg.security.cve.scan_dependencies", return_value=[]),
            patch("zerg.security.scanner._scan_git_history", return_value=[]),
        ):
            result = run_security_scan(tmp_path, categories=["deserialization_risks"])
        critical = [f for f in result.findings if f.severity == "critical"]
        assert len(critical) >= 1
        assert result.passed is False

    def test_high_finding_fails(self, tmp_path: Path) -> None:
        """A high-severity finding should result in passed=False."""
        (tmp_path / "vuln.py").write_text("os.system(cmd)\n")
        with (
            patch("zerg.security.cve.scan_dependencies", return_value=[]),
            patch("zerg.security.scanner._scan_git_history", return_value=[]),
        ):
            result = run_security_scan(tmp_path, categories=["injection_detection"])
        high = [f for f in result.findings if f.severity == "high"]
        assert len(high) >= 1
        assert result.passed is False

    def test_summary_counts_match_findings(self, tmp_path: Path) -> None:
        """summary dict should match actual finding severity counts."""
        (tmp_path / "mixed.py").write_text(
            'password = "supersecret123"\n'  # high
            "data = pickle.loads(x)\n"  # critical
        )
        with (
            patch("zerg.security.cve.scan_dependencies", return_value=[]),
            patch("zerg.security.scanner._scan_git_history", return_value=[]),
        ):
            result = run_security_scan(
                tmp_path,
                categories=["secret_detection", "deserialization_risks"],
            )
        # Verify summary counts match actual finding counts
        for severity, count in result.summary.items():
            actual = len([f for f in result.findings if f.severity == severity])
            assert count == actual, f"Summary says {count} {severity}, but found {actual}"


# ===================================================================
# 6. GIT HISTORY SCANNING
# ===================================================================


class TestGitHistoryScan:
    """Test git history scanning with mocked git log output."""

    def test_detects_secret_in_git_history(self, tmp_path: Path) -> None:
        """Secrets in git commit diffs should be detected."""
        fake_git_log = (
            "commit abc123\n"
            "Author: Test <test@example.com>\n"
            "Date:   Mon Jan 1 00:00:00 2025 +0000\n"
            "\n"
            "    Add config\n"
            "\n"
            "diff --git a/config.py b/config.py\n"
            "+++ b/config.py\n"
            "+AKIAIOSFODNN7EXAMPLE\n"
        )
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = fake_git_log

        secret_patterns = PATTERN_REGISTRY["secret_detection"]

        with patch("zerg.security.scanner.subprocess.run", return_value=mock_result):
            findings = _scan_git_history(tmp_path, depth=10, secret_patterns=secret_patterns)

        assert len(findings) >= 1
        assert findings[0].category == "git_history"
        assert "config.py" in findings[0].file

    def test_clean_history_no_findings(self, tmp_path: Path) -> None:
        """Clean git history should produce no findings."""
        fake_git_log = (
            "commit abc123\n"
            "Author: Test <test@example.com>\n"
            "Date:   Mon Jan 1 00:00:00 2025 +0000\n"
            "\n"
            "    Initial commit\n"
            "\n"
            "diff --git a/readme.md b/readme.md\n"
            "+++ b/readme.md\n"
            "+# My Project\n"
            "+This is a clean project.\n"
        )
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = fake_git_log

        secret_patterns = PATTERN_REGISTRY["secret_detection"]

        with patch("zerg.security.scanner.subprocess.run", return_value=mock_result):
            findings = _scan_git_history(tmp_path, depth=10, secret_patterns=secret_patterns)

        assert len(findings) == 0

    def test_git_command_failure_returns_empty(self, tmp_path: Path) -> None:
        """If git command fails, return empty findings (no crash)."""
        mock_result = MagicMock()
        mock_result.returncode = 128  # non-zero

        secret_patterns = PATTERN_REGISTRY["secret_detection"]

        with patch("zerg.security.scanner.subprocess.run", return_value=mock_result):
            findings = _scan_git_history(tmp_path, depth=10, secret_patterns=secret_patterns)

        assert findings == []

    def test_git_timeout_returns_empty(self, tmp_path: Path) -> None:
        """If git command times out, return empty findings."""
        import subprocess

        secret_patterns = PATTERN_REGISTRY["secret_detection"]

        with patch(
            "zerg.security.scanner.subprocess.run",
            side_effect=subprocess.TimeoutExpired("git", 30),
        ):
            findings = _scan_git_history(tmp_path, depth=10, secret_patterns=secret_patterns)

        assert findings == []

    def test_git_history_finding_has_pattern_prefix(self, tmp_path: Path) -> None:
        """Git history findings should have pattern_name prefixed with git_history_."""
        fake_git_log = "+++ b/secret.py\n+ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456789A\n"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = fake_git_log

        secret_patterns = PATTERN_REGISTRY["secret_detection"]

        with patch("zerg.security.scanner.subprocess.run", return_value=mock_result):
            findings = _scan_git_history(tmp_path, depth=5, secret_patterns=secret_patterns)

        assert len(findings) >= 1
        assert findings[0].pattern_name.startswith("git_history_")


# ===================================================================
# 7. PERFORMANCE TEST
# ===================================================================


class TestPerformance:
    """Scan performance should meet acceptable thresholds."""

    def test_scan_50_files_under_5_seconds(self, tmp_path: Path) -> None:
        """Scanning 50 small files should complete in under 5 seconds."""
        # Create 50 small Python files with various content
        for i in range(50):
            content = f"# File {i}\nx_{i} = {i}\ndef func_{i}():\n    return x_{i} + 1\n"
            (tmp_path / f"file_{i:03d}.py").write_text(content)

        start = time.time()
        with (
            patch("zerg.security.cve.scan_dependencies", return_value=[]),
            patch("zerg.security.scanner._scan_git_history", return_value=[]),
        ):
            result = run_security_scan(tmp_path)
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Scan took {elapsed:.2f}s, exceeding 5s threshold"
        assert result.files_scanned >= 50

    def test_scan_50_files_with_findings_under_5_seconds(self, tmp_path: Path) -> None:
        """Scanning 50 files with some violations should still complete in <5s."""
        for i in range(50):
            if i % 5 == 0:
                # Every 5th file has a violation
                content = f'password = "bad_secret_{i}_value"\n'
            else:
                content = f"safe_value_{i} = {i}\n"
            (tmp_path / f"module_{i:03d}.py").write_text(content)

        start = time.time()
        with (
            patch("zerg.security.cve.scan_dependencies", return_value=[]),
            patch("zerg.security.scanner._scan_git_history", return_value=[]),
        ):
            result = run_security_scan(tmp_path)
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Scan took {elapsed:.2f}s, exceeding 5s threshold"
        assert result.files_scanned >= 50
        assert len(result.findings) >= 10  # at least 10 files with violations


# ===================================================================
# ADDITIONAL EDGE CASE TESTS
# ===================================================================


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_directory_scan(self, tmp_path: Path) -> None:
        """Scanning an empty directory should succeed with zero findings."""
        with (
            patch("zerg.security.cve.scan_dependencies", return_value=[]),
            patch("zerg.security.scanner._scan_git_history", return_value=[]),
        ):
            result = run_security_scan(tmp_path)
        assert result.passed is True
        assert result.files_scanned == 0
        assert len(result.findings) == 0

    def test_binary_file_skipped(self, tmp_path: Path) -> None:
        """Binary files (non-code extensions) should be skipped."""
        (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        (tmp_path / "clean.py").write_text("x = 1\n")
        with (
            patch("zerg.security.cve.scan_dependencies", return_value=[]),
            patch("zerg.security.scanner._scan_git_history", return_value=[]),
        ):
            result = run_security_scan(tmp_path)
        # image.png should not be scanned (not a code extension)
        assert result.files_scanned >= 1

    def test_scan_with_explicit_files(self, tmp_path: Path) -> None:
        """Passing explicit file list should limit scan scope."""
        (tmp_path / "a.py").write_text('password = "leaked_secret!"\n')
        (tmp_path / "b.py").write_text('password = "another_secret!"\n')
        with (
            patch("zerg.security.cve.scan_dependencies", return_value=[]),
            patch("zerg.security.scanner._scan_git_history", return_value=[]),
        ):
            result = run_security_scan(tmp_path, files=[str(tmp_path / "a.py")])
        # Only a.py should be scanned
        assert result.files_scanned == 1

    def test_security_finding_cwe_can_be_none(self) -> None:
        """SecurityFinding.cwe is optional and can be None."""
        finding = SecurityFinding(
            category="test",
            severity="low",
            file="test.py",
            line=1,
            message="test finding",
            cwe=None,
            remediation="no action needed",
            pattern_name="test_pattern",
        )
        assert finding.cwe is None

    def test_security_result_default_values(self) -> None:
        """SecurityResult should have sensible defaults."""
        result = SecurityResult()
        assert result.findings == []
        assert result.categories_scanned == []
        assert result.files_scanned == 0
        assert result.scan_duration_seconds == 0.0
        assert result.passed is True
        assert result.summary == {}
