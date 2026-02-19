"""Security pattern registry for ZERG.

Declarative pattern definitions for 15 capability areas. Capabilities 7 (CVE
scanning) and 10 (git history scanning) are handled by cve.py and scanner.py
respectively, so 13 pattern-based categories live here.

Each pattern carries metadata (CWE, remediation, severity) so the scanner
engine can produce structured SecurityFinding objects without per-category
logic.

WARNING: All regexes are compiled at import time. Avoid nested quantifiers
that could cause ReDoS (e.g. ``(a+)+``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SecurityPattern:
    """A single security pattern with metadata for structured reporting."""

    name: str
    category: str
    regex: re.Pattern[str]
    severity: str  # "critical", "high", "medium", "low", "info"
    message: str
    cwe: str | None
    remediation: str
    file_extensions: set[str] | None = field(default=None)  # None = all files


# ---------------------------------------------------------------------------
# Helper to reduce boilerplate
# ---------------------------------------------------------------------------


def _p(
    name: str,
    category: str,
    pattern: str,
    severity: str,
    message: str,
    cwe: str | None,
    remediation: str,
    *,
    flags: int = 0,
    extensions: set[str] | None = None,
) -> SecurityPattern:
    """Shorthand factory for SecurityPattern construction."""
    return SecurityPattern(
        name=name,
        category=category,
        regex=re.compile(pattern, flags),
        severity=severity,
        message=message,
        cwe=cwe,
        remediation=remediation,
        file_extensions=extensions,
    )


# ===================================================================
# 1. SECRET DETECTION
#    Consolidates SECRET_PATTERNS + HOOK_PATTERNS.security from scanner.py
# ===================================================================

_SECRET_DETECTION: list[SecurityPattern] = [
    _p(
        name="aws_access_key",
        category="secret_detection",
        pattern=r"AKIA[A-Z0-9]{16}",
        severity="critical",
        message="AWS Access Key ID detected",
        cwe="CWE-798",
        remediation="Remove hardcoded AWS key; use IAM roles or environment variables via a secrets manager",
    ),
    _p(
        name="github_pat",
        category="secret_detection",
        pattern=r"ghp_[a-zA-Z0-9]{36}",
        severity="critical",
        message="GitHub Personal Access Token detected",
        cwe="CWE-798",
        remediation="Revoke the token immediately and use GitHub Apps or fine-grained PATs via secrets manager",
    ),
    _p(
        name="github_pat_v2",
        category="secret_detection",
        pattern=r"github_pat_[a-zA-Z0-9]{20,}_[a-zA-Z0-9]{40,}",
        severity="critical",
        message="GitHub fine-grained Personal Access Token detected",
        cwe="CWE-798",
        remediation="Revoke the token immediately and inject via secrets manager",
    ),
    _p(
        name="github_oauth",
        category="secret_detection",
        pattern=r"gho_[a-zA-Z0-9]{36}",
        severity="critical",
        message="GitHub OAuth Token detected",
        cwe="CWE-798",
        remediation="Revoke the token and use OAuth flow with proper token storage",
    ),
    _p(
        name="openai_key",
        category="secret_detection",
        pattern=r"sk-[a-zA-Z0-9]{48}",
        severity="critical",
        message="OpenAI API key detected",
        cwe="CWE-798",
        remediation="Rotate the key immediately; inject via environment variable",
    ),
    _p(
        name="anthropic_key",
        category="secret_detection",
        pattern=r"sk-ant-[a-zA-Z0-9\-]{90,}",
        severity="critical",
        message="Anthropic API key detected",
        cwe="CWE-798",
        remediation="Rotate the key immediately; inject via environment variable",
    ),
    _p(
        name="private_key_header",
        category="secret_detection",
        pattern=r"-----BEGIN (RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----",
        severity="critical",
        message="Private key detected in source",
        cwe="CWE-798",
        remediation="Remove the key from source control; use a secrets manager or SSH agent",
        flags=re.IGNORECASE,
    ),
    _p(
        name="generic_password",
        category="secret_detection",
        pattern=r"password\s*[=:]\s*['\"][^'\"]{8,}['\"]",
        severity="high",
        message="Hardcoded password detected",
        cwe="CWE-798",
        remediation="Move password to environment variable or secrets manager",
        flags=re.IGNORECASE,
    ),
    _p(
        name="generic_secret",
        category="secret_detection",
        pattern=r"secret\s*[=:]\s*['\"][^'\"]{8,}['\"]",
        severity="high",
        message="Hardcoded secret value detected",
        cwe="CWE-798",
        remediation="Move secret to environment variable or secrets manager",
        flags=re.IGNORECASE,
    ),
    _p(
        name="generic_api_key",
        category="secret_detection",
        pattern=r"api_?key\s*[=:]\s*['\"][^'\"]{16,}['\"]",
        severity="high",
        message="Hardcoded API key detected",
        cwe="CWE-798",
        remediation="Move API key to environment variable or secrets manager",
        flags=re.IGNORECASE,
    ),
    _p(
        name="generic_access_token",
        category="secret_detection",
        pattern=r"access_?token\s*[=:]\s*['\"][^'\"]{16,}['\"]",
        severity="high",
        message="Hardcoded access token detected",
        cwe="CWE-798",
        remediation="Move token to environment variable or secrets manager",
        flags=re.IGNORECASE,
    ),
    _p(
        name="generic_auth_token",
        category="secret_detection",
        pattern=r"auth_?token\s*[=:]\s*['\"][^'\"]{16,}['\"]",
        severity="high",
        message="Hardcoded auth token detected",
        cwe="CWE-798",
        remediation="Move token to environment variable or secrets manager",
        flags=re.IGNORECASE,
    ),
    _p(
        name="generic_private_key",
        category="secret_detection",
        pattern=r"private_?key\s*[=:]\s*['\"][^'\"]{16,}['\"]",
        severity="high",
        message="Hardcoded private key value detected",
        cwe="CWE-798",
        remediation="Move private key to a secrets manager; never embed in source",
        flags=re.IGNORECASE,
    ),
    _p(
        name="slack_token",
        category="secret_detection",
        pattern=r"xox[bporas]-[0-9]{10,13}-[a-zA-Z0-9-]{20,}",
        severity="critical",
        message="Slack token detected",
        cwe="CWE-798",
        remediation="Revoke the Slack token and rotate via Slack admin",
    ),
    _p(
        name="stripe_key",
        category="secret_detection",
        pattern=r"(?:sk|pk)_(?:live|test)_[a-zA-Z0-9]{20,}",
        severity="critical",
        message="Stripe API key detected",
        cwe="CWE-798",
        remediation="Rotate the Stripe key; use restricted keys with minimal permissions",
    ),
]


# ===================================================================
# 2. INJECTION DETECTION
#    Shell injection, code injection, SQL injection
# ===================================================================

_INJECTION_DETECTION: list[SecurityPattern] = [
    _p(
        name="shell_injection_true",
        category="injection_detection",
        pattern=r"shell\s*=\s*True",
        severity="high",
        message="subprocess call with shell=True enables shell injection",
        cwe="CWE-78",
        remediation="Use subprocess with shell=False and pass arguments as a list",
        extensions={".py"},
    ),
    _p(
        name="os_system_call",
        category="injection_detection",
        pattern=r"os\.system\s*\(",
        severity="high",
        message="os.system() is vulnerable to shell injection",
        cwe="CWE-78",
        remediation="Use subprocess.run() with a list of arguments instead of os.system()",
        extensions={".py"},
    ),
    _p(
        name="os_popen_call",
        category="injection_detection",
        pattern=r"os\.popen\s*\(",
        severity="high",
        message="os.popen() is vulnerable to shell injection",
        cwe="CWE-78",
        remediation="Use subprocess.run() with a list of arguments instead of os.popen()",
        extensions={".py"},
    ),
    _p(
        name="python_eval",
        category="injection_detection",
        pattern=r"^[^#]*\beval\s*\(",
        severity="high",
        message="eval() can run arbitrary code",
        cwe="CWE-94",
        remediation="Use ast.literal_eval() for data parsing, or a safer alternative",
        extensions={".py"},
    ),
    _p(
        name="python_exec",
        category="injection_detection",
        pattern=r"^[^#]*\bexec\s*\(",
        severity="high",
        message="exec() can run arbitrary code",
        cwe="CWE-94",
        remediation="Avoid exec(); use explicit logic or safe dispatch patterns",
        extensions={".py"},
    ),
    _p(
        name="js_eval",
        category="injection_detection",
        pattern=r"^[^/]*\beval\s*\(",
        severity="high",
        message="eval() can run arbitrary JavaScript code",
        cwe="CWE-94",
        remediation="Use JSON.parse() for data, or a Map-based dispatch for dynamic logic",
        extensions={".js", ".ts", ".jsx", ".tsx"},
    ),
    _p(
        name="sql_string_format",
        category="injection_detection",
        pattern=r"""f['\"]SELECT\s.*WHERE\s.*\{""",
        severity="high",
        message="SQL query built with f-string is vulnerable to SQL injection",
        cwe="CWE-89",
        remediation="Use parameterized queries (cursor.execute with %s or ? placeholders)",
        extensions={".py"},
    ),
    _p(
        name="sql_percent_format",
        category="injection_detection",
        pattern=r"""['\"]SELECT\s.*WHERE\s.*%s['\"].*%\s""",
        severity="medium",
        message="SQL query built with % operator may be vulnerable to SQL injection",
        cwe="CWE-89",
        remediation="Use parameterized queries instead of string formatting with %",
        extensions={".py"},
    ),
    _p(
        name="js_innerhtml_assignment",
        category="injection_detection",
        pattern=r"\.innerHTML\s*=",
        severity="medium",
        message="Direct innerHTML assignment can enable XSS",
        cwe="CWE-79",
        remediation="Use textContent for plain text, or DOMPurify.sanitize() for HTML",
        extensions={".js", ".ts", ".jsx", ".tsx"},
    ),
    _p(
        name="js_document_write",
        category="injection_detection",
        pattern=r"document\.write\s*\(",
        severity="medium",
        message="document.write() can enable XSS",
        cwe="CWE-79",
        remediation="Use DOM manipulation methods (createElement, textContent) instead",
        extensions={".js", ".ts", ".jsx", ".tsx", ".html"},
    ),
]


# ===================================================================
# 3. DESERIALIZATION RISKS
#    Unsafe deserialization (pickle, yaml.load, etc.)
# ===================================================================

_DESERIALIZATION_RISKS: list[SecurityPattern] = [
    _p(
        name="pickle_load",
        category="deserialization_risks",
        pattern=r"pickle\.(?:load|loads)\s*\(",
        severity="critical",
        message="pickle.load/loads can run arbitrary code during deserialization",
        cwe="CWE-502",
        remediation="Use json.loads() or yaml.safe_load() for untrusted data",
        extensions={".py"},
    ),
    _p(
        name="pickle_unpickler",
        category="deserialization_risks",
        pattern=r"pickle\.Unpickler\s*\(",
        severity="critical",
        message="pickle.Unpickler can run arbitrary code during deserialization",
        cwe="CWE-502",
        remediation="Use json or yaml.safe_load() for untrusted data",
        extensions={".py"},
    ),
    _p(
        name="yaml_unsafe_load",
        category="deserialization_risks",
        pattern=r"yaml\.load\s*\([^)]*\bLoader\s*=\s*yaml\.(?:FullLoader|UnsafeLoader|Loader)\b",
        severity="high",
        message="yaml.load with unsafe Loader can run arbitrary Python",
        cwe="CWE-502",
        remediation="Use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader)",
        extensions={".py"},
    ),
    _p(
        name="yaml_load_no_loader",
        category="deserialization_risks",
        pattern=r"yaml\.load\s*\([^)]*\)(?!.*Loader)",
        severity="high",
        message="yaml.load without explicit SafeLoader is unsafe",
        cwe="CWE-502",
        remediation="Use yaml.safe_load() instead of yaml.load()",
        extensions={".py"},
    ),
    _p(
        name="shelve_open",
        category="deserialization_risks",
        pattern=r"shelve\.open\s*\(",
        severity="high",
        message="shelve uses pickle internally and can run arbitrary code",
        cwe="CWE-502",
        remediation="Use a safer storage format (JSON, SQLite) for untrusted data",
        extensions={".py"},
    ),
    _p(
        name="marshal_loads",
        category="deserialization_risks",
        pattern=r"marshal\.loads?\s*\(",
        severity="high",
        message="marshal module can run arbitrary code during deserialization",
        cwe="CWE-502",
        remediation="Use json.loads() for untrusted data",
        extensions={".py"},
    ),
]


# ===================================================================
# 4. CRYPTOGRAPHIC MISUSE
#    MD5/SHA1 for passwords, hardcoded IVs, weak algorithms
# ===================================================================

_CRYPTOGRAPHIC_MISUSE: list[SecurityPattern] = [
    _p(
        name="md5_password_hash",
        category="cryptographic_misuse",
        pattern=r"(?:hashlib\.md5|MD5\.new)\s*\(",
        severity="high",
        message="MD5 is cryptographically broken; do not use for passwords or integrity",
        cwe="CWE-327",
        remediation="Use bcrypt or argon2 for passwords; SHA-256+ for integrity checks",
        extensions={".py"},
    ),
    _p(
        name="sha1_usage",
        category="cryptographic_misuse",
        pattern=r"(?:hashlib\.sha1|SHA1\.new)\s*\(",
        severity="medium",
        message="SHA-1 is deprecated for security-sensitive operations",
        cwe="CWE-328",
        remediation="Use SHA-256 or SHA-3 for integrity checks; bcrypt/argon2 for passwords",
        extensions={".py"},
    ),
    _p(
        name="des_encryption",
        category="cryptographic_misuse",
        pattern=r"(?:from\s+Crypto\.Cipher\s+import\s+DES|DES\.new\s*\()",
        severity="high",
        message="DES encryption is broken and should not be used",
        cwe="CWE-327",
        remediation="Use AES-256 (Fernet or AES-GCM) for symmetric encryption",
        extensions={".py"},
    ),
    _p(
        name="hardcoded_iv",
        category="cryptographic_misuse",
        pattern=r"(?:iv|IV|nonce)\s*=\s*b['\"][^'\"]{8,}['\"]",
        severity="high",
        message="Hardcoded initialization vector (IV) or nonce weakens encryption",
        cwe="CWE-329",
        remediation="Generate a random IV/nonce with os.urandom() for each encryption operation",
        extensions={".py"},
    ),
    _p(
        name="weak_secret_key",
        category="cryptographic_misuse",
        pattern=r"SECRET_KEY\s*=\s*['\"](?:dev|secret|changeme|password|test|admin)['\"]",
        severity="high",
        message="Weak or default SECRET_KEY detected",
        cwe="CWE-798",
        remediation="Use secrets.token_hex(32) to generate a strong secret key",
        extensions={".py"},
    ),
    _p(
        name="math_random_security",
        category="cryptographic_misuse",
        pattern=r"Math\.random\s*\(\)",
        severity="medium",
        message="Math.random() is not cryptographically secure",
        cwe="CWE-330",
        remediation="Use crypto.getRandomValues() or crypto.randomUUID() for security contexts",
        extensions={".js", ".ts", ".jsx", ".tsx"},
    ),
    _p(
        name="python_random_security",
        category="cryptographic_misuse",
        pattern=r"\brandom\.(?:randint|choice|random|choices|sample)\s*\(",
        severity="low",
        message="random module is not cryptographically secure; review if used for security",
        cwe="CWE-330",
        remediation="Use secrets module for tokens, keys, or other security-sensitive values",
        extensions={".py"},
    ),
]


# ===================================================================
# 5. ERROR HANDLING
#    Bare except, fail-open patterns, stack trace leakage
# ===================================================================

_ERROR_HANDLING: list[SecurityPattern] = [
    _p(
        name="bare_except",
        category="error_handling",
        pattern=r"^\s*except\s*:",
        severity="medium",
        message="Bare except catches all exceptions including SystemExit and KeyboardInterrupt",
        cwe="CWE-755",
        remediation="Catch specific exceptions: except (ValueError, KeyError) as e:",
        extensions={".py"},
    ),
    _p(
        name="except_pass",
        category="error_handling",
        pattern=r"except[^:]*:\s*\n\s+pass\s*$",
        severity="medium",
        message="Silently swallowing exceptions hides errors and potential security issues",
        cwe="CWE-755",
        remediation="Log the exception or handle it explicitly; do not silently ignore",
        flags=re.MULTILINE,
        extensions={".py"},
    ),
    _p(
        name="fail_open_return_true",
        category="error_handling",
        pattern=r"except[^:]*:\s*\n\s+return\s+True",
        severity="high",
        message="Returning True on exception is a fail-open pattern (grants access on error)",
        cwe="CWE-755",
        remediation="Fail closed: return False or re-raise the exception on authorization errors",
        flags=re.MULTILINE,
        extensions={".py"},
    ),
    _p(
        name="traceback_in_response",
        category="error_handling",
        pattern=r"traceback\.format_exc\s*\(\)",
        severity="medium",
        message="Exposing tracebacks in responses leaks internal implementation details",
        cwe="CWE-209",
        remediation="Log tracebacks server-side; return a generic error message to clients",
        extensions={".py"},
    ),
    _p(
        name="debug_true_production",
        category="error_handling",
        pattern=r"DEBUG\s*=\s*True",
        severity="medium",
        message="DEBUG=True should not be set in production; exposes stack traces and internals",
        cwe="CWE-209",
        remediation="Set DEBUG=False in production; use environment variables for configuration",
        extensions={".py"},
    ),
]


# ===================================================================
# 6. INPUT VALIDATION
#    Unvalidated user input to dangerous sinks
# ===================================================================

_INPUT_VALIDATION: list[SecurityPattern] = [
    _p(
        name="open_user_path",
        category="input_validation",
        pattern=r"open\s*\(\s*(?:request\.|user_|input|args\[)",
        severity="high",
        message="Opening files based on unvalidated user input enables path traversal",
        cwe="CWE-22",
        remediation="Validate and sanitize the path; ensure it resolves within an allowed directory",
        extensions={".py"},
    ),
    _p(
        name="redirect_unvalidated",
        category="input_validation",
        pattern=r"redirect\s*\(\s*(?:request\.(?:args|form|GET)|params\[)",
        severity="medium",
        message="Unvalidated redirect URL can enable open redirect attacks",
        cwe="CWE-601",
        remediation="Validate redirect URLs against an allowlist of domains",
        extensions={".py", ".js", ".ts"},
    ),
    _p(
        name="requests_get_user_url",
        category="input_validation",
        pattern=r"requests\.(?:get|post|put|delete)\s*\(\s*(?:url|user_|input)",
        severity="medium",
        message="Server-side request with unvalidated URL may enable SSRF",
        cwe="CWE-918",
        remediation="Validate URL against an allowlist; block internal/private IP ranges",
        extensions={".py"},
    ),
    _p(
        name="cors_wildcard_credentials",
        category="input_validation",
        pattern=r"""(?:Access-Control-Allow-Origin['":\s]+\*|origin:\s*['"]?\*['"]?)""",
        severity="medium",
        message="CORS wildcard origin with credentials allows cross-origin attacks",
        cwe="CWE-942",
        remediation="Specify explicit allowed origins instead of wildcard",
        extensions={".py", ".js", ".ts", ".json", ".yaml", ".yml"},
    ),
]


# ===================================================================
# 8. LOCKFILE INTEGRITY
#    Missing lockfiles, unpinned dependencies
# ===================================================================

_LOCKFILE_INTEGRITY: list[SecurityPattern] = [
    _p(
        name="unpinned_pip_install",
        category="lockfile_integrity",
        pattern=r"pip\s+install\s+(?!-r\b|--require-hashes)[a-zA-Z][a-zA-Z0-9_-]*\s*$",
        severity="medium",
        message="Unpinned pip install may pull unexpected versions",
        cwe="CWE-829",
        remediation="Pin exact versions: pip install package==1.2.3 or use requirements.txt with hashes",
        flags=re.MULTILINE,
        extensions={".sh", ".bash", ".yml", ".yaml", ".cfg", ".toml"},
    ),
    _p(
        name="requirements_no_pin",
        category="lockfile_integrity",
        pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*\s*$",
        severity="medium",
        message="Dependency without version pin in requirements file",
        cwe="CWE-829",
        remediation="Pin to exact version: package==1.2.3",
        flags=re.MULTILINE,
        extensions={".txt"},
    ),
    _p(
        name="npm_install_no_save_exact",
        category="lockfile_integrity",
        pattern=r"npm\s+install\s+(?!.*--save-exact)[a-zA-Z@][^\s]*\s*$",
        severity="low",
        message="npm install without --save-exact may use semver ranges",
        cwe="CWE-829",
        remediation="Use npm ci for reproducible installs or npm install --save-exact",
        flags=re.MULTILINE,
        extensions={".sh", ".bash", ".yml", ".yaml"},
    ),
    _p(
        name="wildcard_version",
        category="lockfile_integrity",
        pattern=r"""['\"](?:\*|latest)['\"]""",
        severity="high",
        message="Wildcard or 'latest' version specifier allows arbitrary dependency versions",
        cwe="CWE-829",
        remediation="Pin to a specific version range or exact version",
        extensions={".json"},
    ),
]


# ===================================================================
# 9. LICENSE COMPLIANCE
#    GPL/AGPL detection in dependency manifests
# ===================================================================

_LICENSE_COMPLIANCE: list[SecurityPattern] = [
    _p(
        name="gpl_license",
        category="license_compliance",
        pattern=r"\bGPL(?:-[23])?\b(?!.*exception)",
        severity="medium",
        message="GPL-licensed dependency detected; may require source disclosure",
        cwe=None,
        remediation="Verify GPL compatibility with your project license; consider alternatives",
        flags=re.IGNORECASE,
        extensions={".json", ".toml", ".cfg", ".txt", ".md"},
    ),
    _p(
        name="agpl_license",
        category="license_compliance",
        pattern=r"\bAGPL\b",
        severity="high",
        message="AGPL-licensed dependency detected; network use triggers copyleft obligations",
        cwe=None,
        remediation="AGPL requires source disclosure for network services; evaluate alternatives",
        flags=re.IGNORECASE,
        extensions={".json", ".toml", ".cfg", ".txt", ".md"},
    ),
    _p(
        name="sspl_license",
        category="license_compliance",
        pattern=r"\bSSPL\b",
        severity="high",
        message="SSPL-licensed dependency detected; restrictive for SaaS/cloud use",
        cwe=None,
        remediation="SSPL restricts offering as a service; evaluate license implications",
        flags=re.IGNORECASE,
        extensions={".json", ".toml", ".cfg", ".txt", ".md"},
    ),
]


# ===================================================================
# 11. SENSITIVE FILES
#     .env, credentials, private keys in repository
# ===================================================================

_SENSITIVE_FILES: list[SecurityPattern] = [
    _p(
        name="env_file",
        category="sensitive_files",
        pattern=r"(?:^|/)\.env(?:\.(?:local|production|development|staging|test))?$",
        severity="high",
        message="Environment file may contain secrets and should not be committed",
        cwe="CWE-538",
        remediation="Add .env* to .gitignore; use a secrets manager for production",
    ),
    _p(
        name="credentials_json",
        category="sensitive_files",
        pattern=r"(?:^|/)(?:credentials|service[_-]account|gcp[_-]key)\.json$",
        severity="critical",
        message="Credentials file detected in repository",
        cwe="CWE-538",
        remediation="Remove from source control; add to .gitignore; use a secrets manager",
    ),
    _p(
        name="private_key_file",
        category="sensitive_files",
        pattern=r"(?:^|/)(?:id_rsa|id_dsa|id_ecdsa|id_ed25519)(?:\.pub)?$",
        severity="critical",
        message="SSH key file detected in repository",
        cwe="CWE-538",
        remediation="Remove from source control; never commit private keys",
    ),
    _p(
        name="npmrc_file",
        category="sensitive_files",
        pattern=r"(?:^|/)\.npmrc$",
        severity="medium",
        message=".npmrc may contain authentication tokens",
        cwe="CWE-538",
        remediation="Add .npmrc to .gitignore if it contains auth tokens",
    ),
    _p(
        name="pypirc_file",
        category="sensitive_files",
        pattern=r"(?:^|/)\.pypirc$",
        severity="medium",
        message=".pypirc may contain PyPI authentication credentials",
        cwe="CWE-538",
        remediation="Add .pypirc to .gitignore; use keyring or token-based auth",
    ),
    _p(
        name="htpasswd_file",
        category="sensitive_files",
        pattern=r"(?:^|/)\.htpasswd$",
        severity="high",
        message=".htpasswd file contains hashed credentials",
        cwe="CWE-538",
        remediation="Remove from source control; manage outside the repository",
    ),
    _p(
        name="pem_key_file",
        category="sensitive_files",
        pattern=r"(?:^|/)[^/]+\.(?:pem|key|p12|pfx|jks)$",
        severity="high",
        message="Certificate or key file detected in repository",
        cwe="CWE-538",
        remediation="Remove from source control; add *.pem, *.key, etc. to .gitignore",
    ),
]


# ===================================================================
# 12. FILE PERMISSIONS
#     World-writable files, overly permissive modes
# ===================================================================

_FILE_PERMISSIONS: list[SecurityPattern] = [
    _p(
        name="chmod_world_writable",
        category="file_permissions",
        pattern=r"chmod\s+(?:0?777|a\+w)",
        severity="high",
        message="World-writable file permission (777 or a+w) is insecure",
        cwe="CWE-732",
        remediation="Use restrictive permissions: chmod 755 for dirs, 644 for files",
        extensions={".sh", ".bash", ".py", ".yml", ".yaml"},
    ),
    _p(
        name="chmod_world_readwrite",
        category="file_permissions",
        pattern=r"chmod\s+0?666",
        severity="medium",
        message="World-readable/writable file permission (666) is insecure",
        cwe="CWE-732",
        remediation="Use restrictive permissions: chmod 644 or 640",
        extensions={".sh", ".bash", ".py", ".yml", ".yaml"},
    ),
    _p(
        name="python_chmod_permissive",
        category="file_permissions",
        pattern=r"os\.chmod\s*\([^,]+,\s*0o?7[67][67]",
        severity="high",
        message="Setting overly permissive file permissions programmatically",
        cwe="CWE-732",
        remediation="Use restrictive permissions: os.chmod(path, 0o644)",
        extensions={".py"},
    ),
    _p(
        name="umask_zero",
        category="file_permissions",
        pattern=r"umask\s+0{1,4}\b",
        severity="high",
        message="umask 0 or 000 disables all permission restrictions for new files",
        cwe="CWE-732",
        remediation="Use a restrictive umask: umask 022 or umask 077",
        extensions={".sh", ".bash", ".py"},
    ),
]


# ===================================================================
# 13. ENV VAR LEAKAGE
#     Logging environment variables that may contain secrets
# ===================================================================

_ENV_VAR_LEAKAGE: list[SecurityPattern] = [
    _p(
        name="log_env_vars",
        category="env_var_leakage",
        pattern=r"(?:print|log(?:ger)?\.(?:info|debug|warning|error))\s*\(.*os\.environ",
        severity="medium",
        message="Logging os.environ may expose secrets in log output",
        cwe="CWE-532",
        remediation="Log only specific non-sensitive environment variables; never dump all env vars",
        extensions={".py"},
    ),
    _p(
        name="print_env_all",
        category="env_var_leakage",
        pattern=r"print\s*\(\s*(?:dict\()?os\.environ",
        severity="high",
        message="Printing all environment variables exposes secrets",
        cwe="CWE-532",
        remediation="Log only specific non-sensitive environment variables by name",
        extensions={".py"},
    ),
    _p(
        name="console_log_env",
        category="env_var_leakage",
        pattern=r"console\.log\s*\(\s*process\.env\s*\)",
        severity="high",
        message="Logging all process.env exposes secrets in console output",
        cwe="CWE-532",
        remediation="Log only specific non-sensitive environment variables by name",
        extensions={".js", ".ts"},
    ),
    _p(
        name="env_in_error_message",
        category="env_var_leakage",
        pattern=r"(?:raise|throw)\s+.*os\.environ|process\.env",
        severity="medium",
        message="Including environment variables in error messages may leak secrets",
        cwe="CWE-209",
        remediation="Do not include env vars in exception messages; log them server-side only",
        extensions={".py", ".js", ".ts"},
    ),
]


# ===================================================================
# 14. DOCKERFILE SECURITY
#     Running as root, no USER directive, privileged mode
# ===================================================================

_DOCKERFILE_SECURITY: list[SecurityPattern] = [
    _p(
        name="user_root",
        category="dockerfile_security",
        pattern=r"^\s*USER\s+root\s*$",
        severity="high",
        message="Dockerfile explicitly sets USER to root",
        cwe="CWE-250",
        remediation="Create and use a non-root user: RUN adduser --system appuser && USER appuser",
        flags=re.MULTILINE,
        extensions={".dockerfile", ""},
    ),
    _p(
        name="privileged_flag",
        category="dockerfile_security",
        pattern=r"--privileged",
        severity="critical",
        message="--privileged flag gives container full host access",
        cwe="CWE-250",
        remediation="Remove --privileged; use --cap-add for specific capabilities only",
        extensions={".yml", ".yaml", ".sh", ".bash"},
    ),
    _p(
        name="cap_add_all",
        category="dockerfile_security",
        pattern=r"--cap-add\s*=?\s*ALL",
        severity="critical",
        message="Adding ALL capabilities is equivalent to --privileged",
        cwe="CWE-250",
        remediation="Add only required capabilities (e.g. --cap-add NET_BIND_SERVICE)",
        extensions={".yml", ".yaml", ".sh", ".bash"},
    ),
    _p(
        name="latest_tag",
        category="dockerfile_security",
        pattern=r"^\s*FROM\s+\S+:latest\s*$",
        severity="medium",
        message="Using :latest tag makes builds non-reproducible",
        cwe="CWE-829",
        remediation="Pin to a specific image version or digest",
        flags=re.MULTILINE,
        extensions={".dockerfile", ""},
    ),
    _p(
        name="add_instead_of_copy",
        category="dockerfile_security",
        pattern=r"^\s*ADD\s+(?!https?://)\S+",
        severity="low",
        message="ADD with local files has implicit tar extraction; prefer COPY",
        cwe=None,
        remediation="Use COPY instead of ADD for local files; ADD is only needed for URL fetches",
        flags=re.MULTILINE,
        extensions={".dockerfile", ""},
    ),
    _p(
        name="apt_get_no_cleanup",
        category="dockerfile_security",
        pattern=r"apt-get\s+install(?!.*&&\s*(?:apt-get\s+clean|rm\s+-rf))",
        severity="low",
        message="apt-get install without cleanup increases image size and attack surface",
        cwe=None,
        remediation="Chain cleanup: apt-get install -y pkg && apt-get clean && rm -rf /var/lib/apt/lists/*",
        extensions={".dockerfile", ""},
    ),
]


# ===================================================================
# 15. SYMLINK ESCAPE
#     Path traversal via symlinks and directory traversal
# ===================================================================

_SYMLINK_ESCAPE: list[SecurityPattern] = [
    _p(
        name="followlinks_true",
        category="symlink_escape",
        pattern=r"os\.walk\s*\([^)]*followlinks\s*=\s*True",
        severity="medium",
        message="os.walk with followlinks=True may traverse outside intended directory",
        cwe="CWE-59",
        remediation="Use followlinks=False and resolve symlinks explicitly with boundary checks",
        extensions={".py"},
    ),
    _p(
        name="path_no_resolve",
        category="symlink_escape",
        pattern=r"os\.path\.join\s*\([^)]*\.\.['\"]",
        severity="medium",
        message="Path join with '..' may enable directory traversal",
        cwe="CWE-22",
        remediation="Resolve the path and verify it stays within the intended directory",
        extensions={".py"},
    ),
    _p(
        name="symlink_creation",
        category="symlink_escape",
        pattern=r"os\.symlink\s*\(",
        severity="low",
        message="Symlink creation should be reviewed for potential path escape",
        cwe="CWE-59",
        remediation="Verify symlink targets resolve within intended boundaries",
        extensions={".py"},
    ),
    _p(
        name="path_join_user_input",
        category="symlink_escape",
        pattern=r"(?:os\.path\.join|Path\()\s*\([^)]*(?:request\.|user_|input\()",
        severity="high",
        message="Path construction with user input may enable directory traversal",
        cwe="CWE-22",
        remediation="Resolve the path and check it is relative to an allowed base directory",
        extensions={".py"},
    ),
]


# ===================================================================
# PATTERN REGISTRY - single source of truth
# ===================================================================

PATTERN_REGISTRY: dict[str, list[SecurityPattern]] = {
    "secret_detection": _SECRET_DETECTION,  # Cap 1
    "injection_detection": _INJECTION_DETECTION,  # Cap 2
    "deserialization_risks": _DESERIALIZATION_RISKS,  # Cap 3
    "cryptographic_misuse": _CRYPTOGRAPHIC_MISUSE,  # Cap 4
    "error_handling": _ERROR_HANDLING,  # Cap 5
    "input_validation": _INPUT_VALIDATION,  # Cap 6
    # Cap 7 (CVE scanning) handled by cve.py
    "lockfile_integrity": _LOCKFILE_INTEGRITY,  # Cap 8
    "license_compliance": _LICENSE_COMPLIANCE,  # Cap 9
    # Cap 10 (git history scanning) handled by scanner.py
    "sensitive_files": _SENSITIVE_FILES,  # Cap 11
    "file_permissions": _FILE_PERMISSIONS,  # Cap 12
    "env_var_leakage": _ENV_VAR_LEAKAGE,  # Cap 13
    "dockerfile_security": _DOCKERFILE_SECURITY,  # Cap 14
    "symlink_escape": _SYMLINK_ESCAPE,  # Cap 15
}


def get_all_patterns() -> list[SecurityPattern]:
    """Return a flat list of all patterns across all categories."""
    return [p for patterns in PATTERN_REGISTRY.values() for p in patterns]


def get_patterns_for_extension(ext: str) -> list[SecurityPattern]:
    """Return patterns applicable to a given file extension.

    Args:
        ext: File extension including the dot (e.g. ".py", ".js").
             Pass empty string for extensionless files (e.g. "Dockerfile").

    Returns:
        List of SecurityPattern objects whose file_extensions is None
        (applies to all files) or contains the given extension.
    """
    return [
        p
        for patterns in PATTERN_REGISTRY.values()
        for p in patterns
        if p.file_extensions is None or ext in p.file_extensions
    ]


def get_categories() -> list[str]:
    """Return the sorted list of registered category names."""
    return sorted(PATTERN_REGISTRY.keys())
