"""Unit tests for CommandExecutor security hardening.

Tests verify that dangerous command prefixes have been removed from the
default allowlist and that the trust_commands deprecation warning is logged.
"""

from unittest.mock import patch

from mahabharatha.command_executor import CommandExecutor


class TestDangerousPrefixesRemoved:
    """Test that dangerous command prefixes are rejected by default."""

    def test_python_c_rejected(self):
        """python -c should be rejected by default allowlist."""
        executor = CommandExecutor()
        is_valid, reason, category = executor.validate_command("python -c 'print(1)'")
        assert not is_valid
        assert "not in allowlist" in reason.lower()

    def test_python3_c_rejected(self):
        """python3 -c should be rejected by default allowlist."""
        executor = CommandExecutor()
        is_valid, reason, category = executor.validate_command("python3 -c 'print(1)'")
        assert not is_valid
        assert "not in allowlist" in reason.lower()

    def test_npx_rejected(self):
        """npx should be rejected by default allowlist."""
        executor = CommandExecutor()
        is_valid, reason, category = executor.validate_command("npx some-package")
        assert not is_valid
        assert "not in allowlist" in reason.lower()


class TestTrustCommandsDeprecation:
    """Test deprecation warning for trust_commands flag."""

    def test_trust_commands_deprecation_warning(self):
        """trust_commands=True should log a deprecation warning."""
        with patch("mahabharatha.command_executor.logger") as mock_logger:
            CommandExecutor(trust_commands=True)
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert "deprecated" in call_args.lower()
            assert "trust_commands" in call_args

    def test_no_warning_when_trust_commands_false(self):
        """trust_commands=False should not log any warning."""
        with patch("mahabharatha.command_executor.logger") as mock_logger:
            CommandExecutor(trust_commands=False)
            # logger.warning should not be called for trust_commands deprecation
            for call in mock_logger.warning.call_args_list:
                assert "deprecated" not in str(call).lower()


class TestAllowedCommandsStillWork:
    """Test that legitimate allowed commands are not affected."""

    def test_pytest_allowed(self):
        """pytest should still be allowed."""
        executor = CommandExecutor()
        is_valid, reason, category = executor.validate_command("pytest tests/")
        assert is_valid

    def test_git_status_allowed(self):
        """git status should still be allowed."""
        executor = CommandExecutor()
        is_valid, reason, category = executor.validate_command("git status")
        assert is_valid

    def test_python_m_pytest_allowed(self):
        """python -m pytest should still be allowed."""
        executor = CommandExecutor()
        is_valid, reason, category = executor.validate_command("python -m pytest tests/")
        assert is_valid

    def test_echo_allowed(self):
        """echo should still be allowed."""
        executor = CommandExecutor()
        is_valid, reason, category = executor.validate_command("echo hello")
        assert is_valid
