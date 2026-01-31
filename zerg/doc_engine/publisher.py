"""GitHub Wiki publishing via git clone/push workflow."""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PublishResult:
    """Outcome of a wiki publish operation."""

    success: bool
    pages_copied: int = 0
    commit_sha: str = ""
    error: str = ""
    dry_run: bool = False
    actions: list[str] = field(default_factory=list)


class WikiPublisher:
    """Publishes generated wiki pages to a GitHub Wiki repository.

    Handles the full clone-copy-commit-push cycle for ``{repo}.wiki.git``
    repositories.  Supports a *dry_run* mode that logs intended actions
    without performing any git operations.
    """

    COMMIT_MESSAGE = "docs: update wiki pages via ZERG doc engine"

    def publish(
        self,
        wiki_dir: Path,
        repo_url: str,
        *,
        dry_run: bool = False,
        commit_message: str | None = None,
    ) -> PublishResult:
        """Publish wiki pages from *wiki_dir* to the remote wiki repo.

        Args:
            wiki_dir: Local directory containing ``.md`` files to publish.
            repo_url: Git URL for the wiki repository.  Should end with
                ``.wiki.git`` (e.g. ``https://github.com/user/repo.wiki.git``).
            dry_run: When ``True``, log what would happen without touching
                the remote repository.
            commit_message: Override the default commit message.

        Returns:
            A :class:`PublishResult` describing the outcome.
        """
        wiki_dir = Path(wiki_dir)
        message = commit_message or self.COMMIT_MESSAGE
        result = PublishResult(success=False, dry_run=dry_run)

        # ----- validate inputs -----
        if not wiki_dir.is_dir():
            result.error = f"wiki_dir does not exist: {wiki_dir}"
            logger.error(result.error)
            return result

        pages = list(wiki_dir.glob("*.md"))
        if not pages:
            result.error = f"No .md files found in {wiki_dir}"
            logger.warning(result.error)
            return result

        if dry_run:
            return self._dry_run(pages, repo_url, message, result)

        return self._publish(pages, repo_url, message, result)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _dry_run(
        self,
        pages: list[Path],
        repo_url: str,
        message: str,
        result: PublishResult,
    ) -> PublishResult:
        """Simulate the publish workflow and record planned actions."""
        result.actions.append(f"git clone {repo_url} <tmpdir>")
        for page in sorted(pages):
            result.actions.append(f"copy {page.name} -> <tmpdir>/{page.name}")
        result.actions.append("git add -A")
        result.actions.append(f'git commit -m "{message}"')
        result.actions.append("git push origin master")

        result.pages_copied = len(pages)
        result.success = True

        logger.info(
            "Dry run: would publish %d pages to %s",
            len(pages),
            repo_url,
        )
        for action in result.actions:
            logger.info("  %s", action)

        return result

    def _publish(
        self,
        pages: list[Path],
        repo_url: str,
        message: str,
        result: PublishResult,
    ) -> PublishResult:
        """Execute the clone-copy-commit-push cycle."""
        tmpdir = None
        try:
            tmpdir = Path(tempfile.mkdtemp(prefix="zerg-wiki-"))
            clone_dir = tmpdir / "wiki"

            # Clone
            self._git(["clone", repo_url, str(clone_dir)])
            logger.info("Cloned wiki repo to %s", clone_dir)

            # Copy pages
            copied = 0
            for page in sorted(pages):
                dest = clone_dir / page.name
                shutil.copy2(page, dest)
                copied += 1
                logger.debug("Copied %s", page.name)
            result.pages_copied = copied

            # Stage, commit, push
            self._git(["add", "-A"], cwd=clone_dir)

            if not self._has_changes(clone_dir):
                logger.info("No changes to commit — wiki is up to date")
                result.success = True
                return result

            self._git(["commit", "-m", message], cwd=clone_dir)
            result.commit_sha = self._rev_parse_head(clone_dir)

            self._git(["push", "origin", "master"], cwd=clone_dir)
            logger.info(
                "Pushed %d pages to %s (commit %s)",
                copied,
                repo_url,
                result.commit_sha[:8],
            )

            result.success = True

        except subprocess.CalledProcessError as exc:
            result.error = (
                f"Git operation failed (exit {exc.returncode}): "
                f"{exc.stderr.strip() if exc.stderr else exc.stdout or ''}"
            )
            logger.error(result.error)

        except OSError as exc:
            result.error = f"File operation failed: {exc}"
            logger.error(result.error)

        finally:
            if tmpdir and tmpdir.exists():
                shutil.rmtree(tmpdir, ignore_errors=True)

        return result

    # ------------------------------------------------------------------
    # Git helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _git(
        args: list[str],
        *,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Run a git command with list arguments (no shell)."""
        cmd = ["git"] + args
        return subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )

    @staticmethod
    def _has_changes(repo_dir: Path) -> bool:
        """Return ``True`` if the working tree has staged changes."""
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=repo_dir,
            capture_output=True,
        )
        # exit code 1 means there are differences
        return result.returncode != 0

    @staticmethod
    def _rev_parse_head(repo_dir: Path) -> str:
        """Return the SHA of HEAD in the given repo."""
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
