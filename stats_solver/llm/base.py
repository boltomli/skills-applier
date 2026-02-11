"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Configuration for LLM provider."""

    host: str = "localhost"
    port: int = 11434
    model: str = "llama3"
    timeout: int = 30
    provider: str = "ollama"

    # Optional API endpoint override
    api_endpoint: str | None = None

    # Model parameters
    temperature: float = 0.7
    max_tokens: int | None = None
    top_p: float = 0.9
    top_k: int | None = None


class LLMResponse(BaseModel):
    """Response from LLM provider."""

    content: str
    model: str
    provider: str
    finish_reason: str | None = None
    tokens_used: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig) -> None:
        """Initialize LLM provider with configuration."""
        self.config = config
        self._client: Any | None = None

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM service is available."""
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to LLM service."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to LLM service."""
        pass

    @abstractmethod
    async def list_models(self) -> list[str]:
        """List available models."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text from LLM."""
        pass

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate JSON response from LLM."""
        pass

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response from chat messages."""
        # Default implementation converts chat to single prompt
        formatted = "\n".join(f"{msg['role']}: {msg['content']}" for msg in messages)
        return await self.generate(
            formatted,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on LLM service."""
        try:
            models = await self.list_models()
            return {
                "available": True,
                "provider": self.config.provider,
                "model": self.config.model,
                "models_count": len(models),
            }
        except Exception as e:
            return {
                "available": False,
                "provider": self.config.provider,
                "error": str(e),
            }

    def _get_endpoint(self) -> str:
        """Get API endpoint URL."""
        if self.config.api_endpoint:
            return self.config.api_endpoint
        return f"http://{self.config.host}:{self.config.port}"
