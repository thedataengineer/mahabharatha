"""Environment variable validation for MAHABHARATHA workers.

Provides allowlists, blocklists, and validation logic for environment
variables passed to worker processes and containers.
"""

from __future__ import annotations

from mahabharatha.logging import get_logger

logger = get_logger("env_validator")

# Allowlisted environment variables that can be set from config
ALLOWED_ENV_VARS = {
    # MAHABHARATHA-specific
    "MAHABHARATHA_WORKER_ID",
    "MAHABHARATHA_FEATURE",
    "MAHABHARATHA_WORKTREE",
    "MAHABHARATHA_BRANCH",
    "MAHABHARATHA_TASK_ID",
    "MAHABHARATHA_SPEC_DIR",
    "MAHABHARATHA_STATE_DIR",
    "MAHABHARATHA_REPO_PATH",
    "MAHABHARATHA_LOG_LEVEL",
    "MAHABHARATHA_DEBUG",
    "MAHABHARATHA_ANALYSIS_DEPTH",
    "MAHABHARATHA_COMPACT_MODE",
    "MAHABHARATHA_MCP_HINT",
    "MAHABHARATHA_TOKEN_BUDGET",
    "MAHABHARATHA_BEHAVIORAL_MODE",
    "MAHABHARATHA_TDD_MODE",
    "MAHABHARATHA_RULES_ENABLED",
    "MAHABHARATHA_LOOP_ENABLED",
    "MAHABHARATHA_LOOP_ITERATIONS",
    "MAHABHARATHA_VERIFICATION_GATES",
    "MAHABHARATHA_STALENESS_THRESHOLD",
    # Claude Code cross-session coordination
    "CLAUDE_CODE_TASK_LIST_ID",
    # Common development env vars
    "CI",
    "DEBUG",
    "LOG_LEVEL",
    "VERBOSE",
    "TERM",
    "COLORTERM",
    "NO_COLOR",
    # API keys (user-provided)
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    # Build/test env vars
    "NODE_ENV",
    "PYTHON_ENV",
    "RUST_BACKTRACE",
    "PYTEST_CURRENT_TEST",
}

# Dangerous environment variables that should NEVER be overridden
DANGEROUS_ENV_VARS = {
    "LD_PRELOAD",
    "LD_LIBRARY_PATH",
    "DYLD_INSERT_LIBRARIES",
    "DYLD_LIBRARY_PATH",
    "PATH",
    "PYTHONPATH",
    "NODE_PATH",
    "HOME",
    "USER",
    "SHELL",
    "TMPDIR",
    "TMP",
    "TEMP",
}

# Container path constants
CONTAINER_HOME_DIR = "/home/worker"
CONTAINER_HEALTH_FILE = "/tmp/.mahabharatha-alive"


def validate_env_vars(env: dict[str, str]) -> dict[str, str]:
    """Validate and filter environment variables.

    Args:
        env: Environment variables to validate

    Returns:
        Validated environment variables
    """
    validated = {}

    for key, value in env.items():
        # Check for dangerous vars
        if key.upper() in DANGEROUS_ENV_VARS:
            logger.warning(f"Blocked dangerous environment variable: {key}")
            continue

        # Check if in allowlist or is a MAHABHARATHA_ prefixed var
        if key.upper() in ALLOWED_ENV_VARS or key.upper().startswith("MAHABHARATHA_"):
            # Validate value doesn't contain shell metacharacters
            if any(c in value for c in [";", "|", "&", "`", "$", "(", ")", "<", ">"]):
                logger.warning(f"Blocked env var with shell metacharacters: {key}")
                continue

            validated[key] = value
        else:
            logger.debug(f"Skipping unlisted environment variable: {key}")

    return validated
