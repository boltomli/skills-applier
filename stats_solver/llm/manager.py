"""LLM manager for model selection and configuration."""

import logging
from typing import Dict, List, Optional

from .base import LLMProvider, LLMConfig
from .factory import create_and_connect, LLMConnectionError

logger = logging.getLogger(__name__)


class LLMManager:
    """Manager for LLM providers and model selection."""

    def __init__(self, config: LLMConfig) -> None:
        """Initialize LLM manager."""
        self.config = config
        self._provider: Optional[LLMProvider] = None
        self._available_models: Optional[List[str]] = None

    async def initialize(self) -> bool:
        """Initialize LLM manager and connect to provider."""
        try:
            self._provider = await create_and_connect(self.config)
            self._available_models = await self._provider.list_models()
            logger.info(f"LLM manager initialized with {len(self._available_models)} models")
            return True
        except LLMConnectionError as e:
            logger.error(f"Failed to initialize LLM manager: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown LLM manager and close connections."""
        if self._provider:
            await self._provider.disconnect()
            self._provider = None
            logger.info("LLM manager shut down")

    @property
    def provider(self) -> LLMProvider:
        """Get the active LLM provider."""
        if not self._provider:
            raise RuntimeError("LLM manager not initialized. Call initialize() first.")
        return self._provider

    @property
    def available_models(self) -> List[str]:
        """Get list of available models."""
        if self._available_models is None:
            raise RuntimeError("LLM manager not initialized. Call initialize() first.")
        return self._available_models

    async def switch_model(self, model_name: str) -> bool:
        """Switch to a different model."""
        if model_name not in self.available_models:
            logger.error(f"Model '{model_name}' not available")
            return False

        logger.info(f"Switching to model: {model_name}")
        self.config.model = model_name
        return True

    async def get_model_info(self, model_name: Optional[str] = None) -> Dict:
        """Get information about a model."""
        model = model_name or self.config.model

        return {
            "name": model,
            "available": model in self.available_models,
            "provider": self.config.provider,
            "current": model == self.config.model,
        }

    async def list_models_with_info(self) -> List[Dict]:
        """List all available models with information."""
        return [
            {
                "name": model,
                "available": True,
                "current": model == self.config.model,
            }
            for model in self.available_models
        ]

    def get_config(self) -> Dict:
        """Get current configuration."""
        return self.config.model_dump()

    def update_config(self, **kwargs) -> None:
        """Update configuration parameters."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated config: {key} = {value}")

    @classmethod
    def from_env(cls) -> "LLMManager":
        """Create LLM manager from environment variables."""
        from dotenv import load_dotenv

        load_dotenv()

        import os

        config = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "ollama"),
            host=os.getenv("LLM_HOST", "localhost"),
            port=int(os.getenv("LLM_PORT", "11434")),
            model=os.getenv("LLM_MODEL", "llama3"),
            timeout=int(os.getenv("LLM_TIMEOUT", "30")),
        )

        return cls(config)
