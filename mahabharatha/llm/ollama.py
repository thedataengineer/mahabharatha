import json
import logging
import random
import time
import urllib.error
import urllib.request
from typing import Any

from mahabharatha.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger("mahabharatha.llm.ollama")


class OllamaProvider(LLMProvider):
    """LLM provider using the Ollama REST API with multi-host support."""

    def __init__(self, model: str = "llama3", hosts: list[str] | None = None):
        self.model = model
        self.hosts = hosts or ["http://localhost:11434"]
        self._random = random

    def invoke(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Invoke Ollama via API, trying available hosts."""
        # Randomly select hosts to distribute load
        hosts_to_try = list(self.hosts)
        self._random.shuffle(hosts_to_try)

        last_error = ""
        for host in hosts_to_try:
            url = f"{host}/api/generate"

            # Merge kwargs into the payload if they are valid Ollama params
            payload = {
                "model": kwargs.get("model", self.model),
                "prompt": prompt,
                "stream": False,
                "options": kwargs.get("options", {}),
            }

            data = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            req = urllib.request.Request(url, data=data, headers=headers)

            logger.info(f"Invoking Ollama ({payload['model']}) at {host}")
            start_time = time.time()

            try:
                # Using a generous timeout for local LLM generation
                timeout = kwargs.get("timeout", 600)
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    resp_body = response.read().decode("utf-8")
                    resp_data = json.loads(resp_body)

                    duration_ms = int((time.time() - start_time) * 1000)

                    return LLMResponse(
                        success=True,
                        stdout=resp_data.get("response", ""),
                        stderr="",
                        exit_code=0,
                        duration_ms=duration_ms,
                        task_id=kwargs.get("task_id"),
                        raw_response=resp_data,
                    )

            except urllib.error.URLError as e:
                logger.warning(f"Ollama host {host} unreachable: {e}")
                last_error = f"Host {host} unreachable: {e}"
                continue
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Ollama host {host} error: {e}")
                last_error = f"Host {host} error: {e}"
                continue

        # If all hosts failed
        duration_ms = int((time.time() - start_time) * 1000) if "start_time" in locals() else 0
        return LLMResponse(
            success=False,
            stdout="",
            stderr=f"All Ollama hosts failed. Last error: {last_error}",
            exit_code=-1,
            duration_ms=duration_ms,
            task_id=kwargs.get("task_id"),
        )

    def warmup(self, model: str | None = None) -> bool:
        """Force load the model into VRAM on all configured hosts."""
        model_name = model or self.model
        logger.info(f"Warming up Ollama model '{model_name}' on all hosts")

        success_count = 0
        for host in self.hosts:
            url = f"{host}/api/generate"
            payload = {"model": model_name, "prompt": "", "stream": False}
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            try:
                # 30s timeout for warmup; it usually returns quickly if loaded,
                # or takes a few seconds to load.
                with urllib.request.urlopen(req, timeout=30) as response:
                    if response.status == 200:
                        success_count += 1
                        logger.info(f"Model '{model_name}' warmed up on {host}")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Warmup failed on {host}: {e}")

        return success_count > 0

    def check_health(self) -> dict[str, Any]:
        """Check if Ollama hosts are reachable and model is available."""
        results = []
        for host in self.hosts:
            host_status = {"host": host, "reachable": False, "models": []}
            try:
                # Check /api/tags for model list
                url = f"{host}/api/tags"
                with urllib.request.urlopen(url, timeout=5) as response:
                    resp_body = response.read().decode("utf-8")
                    resp_data = json.loads(resp_body)
                    host_status["reachable"] = True
                    # In Ollama API, models are in 'models' list, each having a 'name'
                    host_status["models"] = [m.get("name") for m in resp_data.get("models", [])]
                    # Also try to match model name precisely or by prefix
                    host_status["has_model"] = any(
                        m == self.model or m.startswith(f"{self.model}:") for m in host_status["models"]
                    )
            except Exception as e:  # noqa: BLE001
                host_status["error"] = str(e)
            results.append(host_status)

        # Overall status is ok if at least one host is reachable and has the model
        any_ok = any(r.get("reachable") and r.get("has_model") for r in results)
        return {
            "status": "ok" if any_ok else "error",
            "provider": "ollama",
            "hosts": results,
            "target_model": self.model,
        }
