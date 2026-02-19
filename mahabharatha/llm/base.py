from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResponse:
    """Standardized response from an LLM provider."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    task_id: str | None = None
    raw_response: Any = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def invoke(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Invoke the LLM with a prompt."""
        pass

    @abstractmethod
    def warmup(self, model: str | None = None) -> bool:
        """Pre-load the model into memory/VRAM."""
        pass

    @abstractmethod
    def check_health(self) -> dict[str, Any]:
        """Check the health and availability of the provider."""
        pass
