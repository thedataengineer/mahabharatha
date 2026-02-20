"""Tests for MAHABHARATHA v2 Git Operations Command."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGitAction:
    """Tests for git action enumeration."""

    def test_actions_exist(self):
        """Test git actions are defined."""
        from git_ops import GitAction

        assert hasattr(GitAction, "COMMIT")
        assert hasattr(GitAction, "BRANCH")
        assert hasattr(GitAction, "MERGE")
        assert hasattr(GitAction, "SYNC")
        assert hasattr(GitAction, "HISTORY")
        assert hasattr(GitAction, "FINISH")


class TestGitConfig:
    """Tests for git configuration."""

    def test_config_defaults(self):
        """Test GitConfig has sensible defaults."""
        from git_ops import GitConfig

        config = GitConfig()
        assert config.push is False
        assert config.base_branch == "main"

    def test_config_custom(self):
        """Test GitConfig with custom values."""
        from git_ops import GitConfig

        config = GitConfig(push=True, base_branch="develop")
        assert config.push is True
        assert config.base_branch == "develop"


class TestCommitMessage:
    """Tests for commit message generation."""

    def test_message_creation(self):
        """Test CommitMessage can be created."""
        from git_ops import CommitMessage

        msg = CommitMessage(
            type="feat",
            scope="auth",
            description="add login endpoint",
        )
        assert msg.type == "feat"

    def test_message_format(self):
        """Test CommitMessage conventional format."""
        from git_ops import CommitMessage

        msg = CommitMessage(
            type="fix",
            scope="api",
            description="handle null response",
        )
        formatted = msg.format()
        assert "fix(api)" in formatted
        assert "handle null response" in formatted


class TestFinishResult:
    """Tests for finish workflow result."""

    def test_result_creation(self):
        """Test FinishResult can be created."""
        from git_ops import FinishResult

        result = FinishResult(
            success=True,
            action="merged",
            message="Branch merged to main",
        )
        assert result.success is True

    def test_result_blocked(self):
        """Test FinishResult when blocked."""
        from git_ops import FinishResult

        result = FinishResult(
            success=False,
            action="blocked",
            message="Tests failing",
            blocked=True,
            reason="3 test failures",
        )
        assert result.blocked is True
        assert result.success is False


class TestFinishOption:
    """Tests for finish workflow options."""

    def test_options_exist(self):
        """Test FinishOption values are defined."""
        from git_ops import FinishOption

        assert hasattr(FinishOption, "MERGE_LOCAL")
        assert hasattr(FinishOption, "CREATE_PR")
        assert hasattr(FinishOption, "KEEP_BRANCH")
        assert hasattr(FinishOption, "DISCARD")


class TestCommitGenerator:
    """Tests for intelligent commit message generation."""

    def test_generator_creation(self):
        """Test CommitGenerator can be created."""
        from git_ops import CommitGenerator

        gen = CommitGenerator()
        assert gen is not None

    def test_detect_commit_type(self):
        """Test detecting commit type from changes."""
        from git_ops import CommitGenerator

        gen = CommitGenerator()
        # New files suggest feat
        commit_type = gen.detect_type(["new_feature.py"], [], [])
        assert commit_type in ["feat", "chore", "docs"]


class TestGitOps:
    """Tests for GitOps class."""

    def test_git_ops_creation(self):
        """Test GitOps can be created."""
        from git_ops import GitOps

        ops = GitOps()
        assert ops is not None

    def test_available_actions(self):
        """Test listing available actions."""
        from git_ops import GitOps

        ops = GitOps()
        actions = ops.available_actions()
        assert "commit" in actions
        assert "finish" in actions

    def test_get_current_branch(self):
        """Test getting current branch."""
        from git_ops import GitOps

        ops = GitOps()
        branch = ops.get_current_branch()
        assert isinstance(branch, str)

    def test_get_status(self):
        """Test getting git status."""
        from git_ops import GitOps

        ops = GitOps()
        status = ops.get_status()
        assert "staged" in status
        assert "modified" in status
        assert "untracked" in status


class TestGitCommand:
    """Tests for GitCommand class."""

    def test_command_creation(self):
        """Test GitCommand can be created."""
        from git_ops import GitCommand

        cmd = GitCommand()
        assert cmd is not None

    def test_command_run_status(self):
        """Test running status action."""
        from git_ops import GitCommand

        cmd = GitCommand()
        result = cmd.run(action="status")
        assert result is not None

    def test_command_format_text(self):
        """Test text output format."""
        from git_ops import FinishResult, GitCommand

        cmd = GitCommand()
        result = FinishResult(
            success=True,
            action="merged",
            message="Done",
        )
        output = cmd.format_result(result, format="text")
        assert "merged" in output.lower() or "Done" in output

    def test_command_format_json(self):
        """Test JSON output format."""
        import json

        from git_ops import FinishResult, GitCommand

        cmd = GitCommand()
        result = FinishResult(
            success=True,
            action="merged",
            message="Done",
        )
        output = cmd.format_result(result, format="json")
        data = json.loads(output)
        assert data["success"] is True
