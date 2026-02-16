"""Unified security package for ZERG.

This package consolidates all security logic:
- scanner.py: Scan functions and pattern constants (from security.py)
- hooks.py: Git hook management (from security.py)
- rules.py: Stack detection and rule fetching (from security_rules.py)

Provides backward-compatible re-exports of all public names.
"""

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Data models (specified in design.md)
# ---------------------------------------------------------------------------


@dataclass
class SecurityFinding:
    """A single security finding from a scan."""

    category: str  # "secret", "injection", "crypto", etc.
    severity: str  # "critical", "high", "medium", "low", "info"
    file: str
    line: int
    message: str
    cwe: str | None  # "CWE-798", etc.
    remediation: str
    pattern_name: str


@dataclass
class SecurityResult:
    """Aggregated results from a security scan."""

    findings: list[SecurityFinding] = field(default_factory=list)
    categories_scanned: list[str] = field(default_factory=list)
    files_scanned: int = 0
    scan_duration_seconds: float = 0.0
    passed: bool = True  # True if no critical/high findings
    summary: dict[str, int] = field(default_factory=dict)  # severity -> count


# ---------------------------------------------------------------------------
# Backward-compatible re-exports from scanner.py
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Backward-compatible re-exports from hooks.py
# ---------------------------------------------------------------------------
from zerg.security.hooks import (  # noqa: E402
    install_hooks,
    uninstall_hooks,
)

# ---------------------------------------------------------------------------
# Backward-compatible re-exports from rules.py
# ---------------------------------------------------------------------------
from zerg.security.rules import (  # noqa: E402
    FRAMEWORK_DETECTION,
    INFRASTRUCTURE_DETECTION,
    LANGUAGE_DETECTION,
    RULE_PATHS,
    RULES_RAW_URL,
    RULES_REPO,
    ProjectStack,
    detect_project_stack,
    fetch_rules,
    filter_rules_for_files,
    generate_claude_md_section,
    get_required_rules,
    integrate_security_rules,
    summarize_rules,
)
from zerg.security.scanner import (  # noqa: E402
    HOOK_PATTERNS,
    SECRET_PATTERNS,
    SENSITIVE_FILES,
    _legacy_scan,
    check_file_size,
    check_for_non_ascii_filenames,
    check_for_secrets,
    check_sensitive_files,
    get_large_files,
    run_security_scan,
    validate_commit_message,
)

__all__ = [
    # Data models
    "SecurityFinding",
    "SecurityResult",
    # Scanner (run_security_scan now returns SecurityResult)
    "SECRET_PATTERNS",
    "HOOK_PATTERNS",
    "SENSITIVE_FILES",
    "check_for_secrets",
    "check_for_non_ascii_filenames",
    "check_sensitive_files",
    "validate_commit_message",
    "check_file_size",
    "get_large_files",
    "run_security_scan",
    "_legacy_scan",
    # Hooks
    "install_hooks",
    "uninstall_hooks",
    # Rules
    "ProjectStack",
    "LANGUAGE_DETECTION",
    "FRAMEWORK_DETECTION",
    "INFRASTRUCTURE_DETECTION",
    "RULE_PATHS",
    "RULES_REPO",
    "RULES_RAW_URL",
    "detect_project_stack",
    "get_required_rules",
    "filter_rules_for_files",
    "summarize_rules",
    "fetch_rules",
    "generate_claude_md_section",
    "integrate_security_rules",
]
