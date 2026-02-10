"""Factory for creating LLM provider instances."""

import logging
from typing import Optional

from .base import LLMProvider, LLMConfig
from .ollama import OllamaProvider
from .lm_studio import LMStudioProvider

logger = logging.getLogger(__name__)


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    pass


class LLMConnectionError(LLMProviderError):
    """Exception raised when connection to LLM fails."""
    pass


class LLMModelNotFoundError(LLMProviderError):
    """Exception raised when requested model is not found."""
    pass


class LLMGenerationError(LLMProviderError):
    """Exception raised when LLM generation fails."""
    pass


def create_provider(config: LLMConfig) -> LLMProvider:
    """Create LLM provider instance based on configuration."""
    provider_map = {
        "ollama": OllamaProvider,
        "lm_studio": LMStudioProvider,
    }
    
    provider_class = provider_map.get(config.provider.lower())
    if not provider_class:
        raise ValueError(f"Unknown LLM provider: {config.provider}")
    
    return provider_class(config)


async def test_connection(config: LLMConfig) -> dict:
    """Test connection to LLM provider and return health status."""
    provider = None
    try:
        provider = create_provider(config)
        
        if not await provider.connect():
            raise LLMConnectionError(f"Failed to connect to {config.provider}")
        
        health = await provider.health_check()
        
        if not health["available"]:
            raise LLMConnectionError(f"{config.provider} service not available")
        
        # Verify model exists
        models = await provider.list_models()
        if config.model not in models:
            available = ", ".join(models[:5])
            if len(models) > 5:
                available += f" ... and {len(models) - 5} more"
            logger.warning(
                f"Model '{config.model}' not found. Available: {available}"
            )
            health["model_found"] = False
        else:
            health["model_found"] = True
        
        return health
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise LLMConnectionError(f"Connection test failed: {e}")
    finally:
        if provider:
            await provider.disconnect()


async def create_and_connect(config: LLMConfig) -> LLMProvider:
    """Create provider and establish connection with error handling."""
    try:
        provider = create_provider(config)
        
        if not await provider.connect():
            raise LLMConnectionError(f"Failed to connect to {config.provider}")
        
        return provider
    except Exception as e:
        logger.error(f"Failed to create and connect provider: {e}")
        raise