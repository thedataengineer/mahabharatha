import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from mahabharatha.llm.base import LLMProvider, LLMResponse
from mahabharatha.protocol_types import CLAUDE_CLI_COMMAND, CLAUDE_CLI_DEFAULT_TIMEOUT

logger = logging.getLogger("mahabharatha.llm.claude")


class ClaudeProvider(LLMProvider):
    """LLM provider using the Claude Code CLI."""

    def __init__(self, worktree_path: Path, worker_id: int):
        self.worktree_path = worktree_path
        self.worker_id = worker_id

    def invoke(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Invoke Claude Code CLI with the prompt."""
        timeout = kwargs.get("timeout", CLAUDE_CLI_DEFAULT_TIMEOUT)
        task_id = kwargs.get("task_id", "unknown")

        cmd = [
            CLAUDE_CLI_COMMAND,
            "--print",
            "--dangerously-skip-permissions",
            prompt,
        ]

        logger.info(f"Invoking Claude Code for worker {self.worker_id}")
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.worktree_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                env={
                    **os.environ,
                    "Mahabharatha_TASK_ID": task_id,
                    "Mahabharatha_WORKER_ID": str(self.worker_id),
                },
            )

            duration_ms = int((time.time() - start_time) * 1000)
            success = result.returncode == 0

            return LLMResponse(
                success=success,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration_ms=duration_ms,
                task_id=task_id,
                raw_response=result,
            )

        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            return LLMResponse(
                success=False,
                stdout="",
                stderr=f"Claude Code invocation timed out after {timeout}s",
                exit_code=-1,
                duration_ms=duration_ms,
            )
        except FileNotFoundError:
            duration_ms = int((time.time() - start_time) * 1000)
            return LLMResponse(
                success=False,
                stdout="",
                stderr="claude command not found",
                exit_code=-1,
                duration_ms=duration_ms,
            )
        except Exception as e:  # noqa: BLE001
            duration_ms = int((time.time() - start_time) * 1000)
            return LLMResponse(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                duration_ms=duration_ms,
            )

    def warmup(self, model: str | None = None) -> bool:
        """Claude CLI doesn't support explicit warmup; no-op."""
        return True

    def check_health(self) -> dict[str, Any]:
        """Check if Claude CLI is accessible."""
        import subprocess

        try:
            # Simple version check to verify installation
            subprocess.run(["claude", "--version"], capture_output=True, check=True)
            return {"status": "ok", "provider": "claude", "cli_found": True}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "provider": "claude", "error": str(e)}
