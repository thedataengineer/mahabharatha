import contextlib
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from mahabharatha.llm.claude import ClaudeProvider
from mahabharatha.llm.ollama import OllamaProvider
from mahabharatha.state.resource_repo import ResourceRepo


class TestOllamaExpansion(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path("/tmp/mahabharatha_test_state")
        self.tmp_dir.mkdir(exist_ok=True, parents=True)
        self.state_file = self.tmp_dir / "state.json"
        if self.state_file.exists():
            self.state_file.unlink()

    def test_ollama_load_balancing(self):
        """Verify that OllamaProvider rotates through multiple hosts."""
        hosts = ["http://host1:11434", "http://host2:11434", "http://host3:11434"]
        provider = OllamaProvider(model="llama3", hosts=hosts)

        with patch("urllib.request.urlopen") as mock_url:
            mock_url.return_value.__enter__.return_value.read.return_value = b'{"response": "ok"}'
            mock_url.return_value.__enter__.return_value.getcode.return_value = 200

            seen_hosts = set()
            for _ in range(20):
                provider.invoke("test prompt")
                arg = mock_url.call_args[0][0]
                # arg might be a string or a urllib.request.Request object
                url = arg.full_url if hasattr(arg, "full_url") else arg
                for h in hosts:
                    if url.startswith(h):
                        seen_hosts.add(h)

            self.assertGreater(len(seen_hosts), 1, "Should have load balanced across multiple hosts")

    def test_resource_repo_semaphore(self):
        """Verify the global resource semaphore limits concurrency."""
        persistence = MagicMock()
        persistence.feature = "test"

        # State data structure as expected by ResourceRepo
        state_data = {"resources": {}}
        persistence.state = state_data

        @contextlib.contextmanager
        def mock_atomic_update():
            # In real PersistenceLayer, atomic_update reloads from disk
            # For this mock, we just yield
            yield

        persistence.atomic_update.side_effect = mock_atomic_update

        repo = ResourceRepo(persistence)

        # Acquire 2 slots for 'ollama'
        self.assertTrue(repo.acquire_slot("ollama", 2, worker_id=1))
        self.assertTrue(repo.acquire_slot("ollama", 2, worker_id=2))

        with patch("time.sleep"):
            # Verify state (modified via self._persistence.state in ResourceRepo)
            self.assertIn("ollama", state_data["resources"])
            self.assertEqual(len(state_data["resources"]["ollama"]["active"]), 2)

            # Release one
            repo.release_slot("ollama", worker_id=1)
            self.assertEqual(len(state_data["resources"]["ollama"]["active"]), 1)

            # Now worker 3 can get in
            self.assertTrue(repo.acquire_slot("ollama", 2, worker_id=3))

    def test_ollama_warmup(self):
        """Verify warmup hits all hosts."""
        hosts = ["http://host1:11434", "http://host2:11434"]
        provider = OllamaProvider(model="llama3", hosts=hosts)

        with patch("urllib.request.urlopen") as mock_url:
            mock_url.return_value.__enter__.return_value.read.return_value = b'{"status": "success"}'
            provider.warmup()

            self.assertEqual(mock_url.call_count, 2)
            urls = []
            for call in mock_url.call_args_list:
                arg = call[0][0]
                urls.append(arg.full_url if hasattr(arg, "full_url") else arg)

            self.assertTrue(any("host1" in u for u in urls))
            self.assertTrue(any("host2" in u for u in urls))

    def test_claude_provider_health(self):
        """Verify Claude health check."""
        # ClaudeProvider needs worktree_path and worker_id
        provider = ClaudeProvider(worktree_path=Path("/tmp"), worker_id=1)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            health = provider.check_health()
            self.assertEqual(health["status"], "ok")
            self.assertTrue(health["cli_found"])


if __name__ == "__main__":
    unittest.main()
