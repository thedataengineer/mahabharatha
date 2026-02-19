"""ZERG CLI commands."""

from mahabharatha.commands.analyze import analyze
from mahabharatha.commands.build import build
from mahabharatha.commands.cleanup import cleanup
from mahabharatha.commands.debug import debug
from mahabharatha.commands.design import design
from mahabharatha.commands.document import document
from mahabharatha.commands.git_cmd import git_cmd
from mahabharatha.commands.health import health
from mahabharatha.commands.init import init
from mahabharatha.commands.install_commands import install_commands, uninstall_commands
from mahabharatha.commands.logs import logs
from mahabharatha.commands.merge_cmd import merge_cmd
from mahabharatha.commands.plan import plan
from mahabharatha.commands.refactor import refactor
from mahabharatha.commands.retry import retry
from mahabharatha.commands.review import review
from mahabharatha.commands.rush import rush
from mahabharatha.commands.security_rules_cmd import security_rules_group
from mahabharatha.commands.status import status
from mahabharatha.commands.stop import stop
from mahabharatha.commands.test_cmd import test_cmd
from mahabharatha.commands.wiki import wiki

__all__ = [
    "analyze",
    "build",
    "cleanup",
    "design",
    "git_cmd",
    "init",
    "logs",
    "merge_cmd",
    "plan",
    "refactor",
    "retry",
    "review",
    "rush",
    "security_rules_group",
    "status",
    "stop",
    "test_cmd",
    "debug",
    "document",
    "health",
    "install_commands",
    "uninstall_commands",
    "wiki",
]
