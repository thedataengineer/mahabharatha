"""E2E tests with real Claude CLI execution.

All tests decorated with @pytest.mark.real_e2e and require either:
- Claude Pro/Team OAuth (claude CLI in PATH)
- ANTHROPIC_API_KEY environment variable

Tests are automatically skipped if neither authentication method is available.
"""

import os
import shutil
from pathlib import Path

import pytest

from tests.e2e.harness import E2EHarness


def _auth_available() -> tuple[bool, str]:
    """Auto-detect available authentication method.

    Returns:
        Tuple of (auth_available, auth_method).
        auth_method is one of: "claude-cli", "api-key", "none"
    """
    # Check for Claude CLI (Pro/Team OAuth)
    if shutil.which("claude") is not None:
        return True, "claude-cli"

    # Check for API key
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True, "api-key"

    return False, "none"


# Check auth availability at module level
_AUTH_AVAILABLE, _AUTH_METHOD = _auth_available()

# Skip marker for tests requiring real authentication
skip_no_auth = pytest.mark.skipif(
    not _AUTH_AVAILABLE,
    reason=(
        "No authentication available. Need either: "
        "claude CLI in PATH (Pro/Team) or ANTHROPIC_API_KEY env var"
    ),
)


@pytest.mark.real_e2e
@skip_no_auth
class TestRealExecution:
    """Real execution tests using Claude CLI with actual API calls.

    These tests are expensive (API tokens) and require authentication.
    Run explicitly with: pytest -m real_e2e
    """

    def test_real_pipeline_with_simple_task(self, tmp_path: Path) -> None:
        """Run real pipeline with 1 worker executing a trivial file creation task.

        Creates a minimal task graph with a single task that writes 'hello world'
        to a file. Uses actual Claude CLI for execution.

        This test validates:
        - Authentication works (auto-detected method)
        - Real Claude CLI can execute ZERG task specs
        - E2E harness works in real mode
        - Task verification passes with real execution
        """
        harness = E2EHarness(tmp_path, feature="real-test", mode="real")
        harness.setup_repo()

        # Define a trivial task: create a file with hello world
        tasks = [
            {
                "id": "REAL-001",
                "title": "Create hello file",
                "description": (
                    "Create a file called hello.txt with the content 'hello world'. "
                    "This is a trivial task to validate real Claude CLI execution."
                ),
                "phase": "implementation",
                "level": 1,
                "dependencies": [],
                "files": {
                    "create": ["hello.txt"],
                    "modify": [],
                    "read": [],
                },
                "verification": {
                    "command": "test -f hello.txt && grep -q 'hello world' hello.txt",
                    "timeout_seconds": 30,
                },
            }
        ]

        harness.setup_task_graph(tasks)

        # NOTE: E2EHarness.run() currently raises NotImplementedError for real mode
        # This test demonstrates the auth detection logic. Full implementation
        # requires integrating actual Claude CLI invocation into the harness.
        with pytest.raises(NotImplementedError, match="Real mode requires Claude CLI"):
            harness.run(workers=1)

        # When real mode is implemented, the test should assert:
        # result = harness.run(workers=1)
        # assert result.success
        # assert result.tasks_completed == 1
        # assert result.tasks_failed == 0
        # assert (harness.repo_path / "hello.txt").exists()
        # assert (harness.repo_path / "hello.txt").read_text() == "hello world"


@pytest.mark.real_e2e
def test_auth_detection() -> None:
    """Verify authentication detection logic works correctly.

    This test runs regardless of auth availability to validate the detection.
    """
    available, method = _auth_available()

    # Should detect at least one method or neither
    assert method in {"claude-cli", "api-key", "none"}

    # Consistency check
    if method == "claude-cli":
        assert available
        assert shutil.which("claude") is not None
    elif method == "api-key":
        assert available
        assert os.environ.get("ANTHROPIC_API_KEY") is not None
    elif method == "none":
        assert not available


@pytest.mark.real_e2e
@skip_no_auth
def test_auth_method_reported(capsys: pytest.CaptureFixture) -> None:
    """Report detected authentication method to test output."""
    print(f"\nAuthentication method: {_AUTH_METHOD}")
    captured = capsys.readouterr()
    assert _AUTH_METHOD in captured.out
