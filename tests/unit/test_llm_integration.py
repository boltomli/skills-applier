"""
Unit tests for LLM integration module.
"""

import pytest
import httpx
from unittest.mock import Mock, patch, MagicMock
from stats_solver.llm.base import LLMProvider, LLMMessage, LLMResponse
from stats_solver.llm.ollama import OllamaProvider
from stats_solver.llm.lm_studio import LMStudioProvider
from stats_solver.llm.factory import LLMProviderFactory
from stats_solver.llm.manager import LLMManager


class TestLLMMessage:
    """Test LLM message class."""

    def test_create_user_message(self):
        """Test creating a user message."""
        message = LLMMessage(role="user", content="Hello")
        assert message.role == "user"
        assert message.content == "Hello"

    def test_create_system_message(self):
        """Test creating a system message."""
        message = LLMMessage(role="system", content="You are helpful")
        assert message.role == "system"
        assert message.content == "You are helpful"


class TestLLMResponse:
    """Test LLM response class."""

    def test_create_response(self):
        """Test creating a response."""
        response = LLMResponse(
            content="Hello there!",
            finish_reason="stop",
            model="llama3",
            usage={"prompt_tokens": 10, "completion_tokens": 5}
        )
        assert response.content == "Hello there!"
        assert response.finish_reason == "stop"
        assert response.model == "llama3"
        assert response.usage["prompt_tokens"] == 10


class TestOllamaProvider:
    """Test Ollama provider."""

    @pytest.fixture
    def provider(self):
        """Create an Ollama provider instance."""
        return OllamaProvider(host="localhost", port=11434, model="llama3")

    def test_initialization(self, provider):
        """Test provider initialization."""
        assert provider.host == "localhost"
        assert provider.port == 11434
        assert provider.model == "llama3"
        assert provider.base_url == "http://localhost:11434"

    @patch('httpx.Client')
    def test_list_models(self, mock_client, provider):
        """Test listing available models."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3"},
                {"name": "mistral"}
            ]
        }
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response

        models = provider.list_models()
        assert len(models) == 2
        assert "llama3" in models
        assert "mistral" in models

    @patch('httpx.Client')
    def test_generate_response(self, mock_client, provider):
        """Test generating a response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "llama3",
            "message": {"role": "assistant", "content": "Hello!"},
            "done": True,
            "prompt_eval_count": 10,
            "eval_count": 5
        }
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        messages = [LLMMessage(role="user", content="Hello")]
        response = provider.generate(messages)

        assert response.content == "Hello!"
        assert response.model == "llama3"
        assert response.finish_reason == "stop"

    @patch('httpx.Client')
    def test_connection_error(self, mock_client, provider):
        """Test handling connection errors."""
        mock_client.return_value.__enter__.return_value.get.side_effect = httpx.ConnectError

        with pytest.raises(ConnectionError):
            provider.list_models()


class TestLMStudioProvider:
    """Test LM Studio provider."""

    @pytest.fixture
    def provider(self):
        """Create an LM Studio provider instance."""
        return LMStudioProvider(host="localhost", port=1234, model="test-model")

    def test_initialization(self, provider):
        """Test provider initialization."""
        assert provider.host == "localhost"
        assert provider.port == 1234
        assert provider.model == "test-model"
        assert provider.base_url == "http://localhost:1234"

    @patch('httpx.Client')
    def test_generate_response(self, mock_client, provider):
        """Test generating a response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "test-id",
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Response!"},
                    "finish_reason": "stop"
                }
            ],
            "model": "test-model",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        messages = [LLMMessage(role="user", content="Test")]
        response = provider.generate(messages)

        assert response.content == "Response!"
        assert response.model == "test-model"


class TestLLMProviderFactory:
    """Test LLM provider factory."""

    def test_create_ollama_provider(self):
        """Test creating an Ollama provider."""
        config = {
            "provider": "ollama",
            "host": "localhost",
            "port": 11434,
            "model": "llama3"
        }
        provider = LLMProviderFactory.create(config)
        assert isinstance(provider, OllamaProvider)

    def test_create_lm_studio_provider(self):
        """Test creating an LM Studio provider."""
        config = {
            "provider": "lm_studio",
            "host": "localhost",
            "port": 1234,
            "model": "test"
        }
        provider = LLMProviderFactory.create(config)
        assert isinstance(provider, LMStudioProvider)

    def test_invalid_provider(self):
        """Test handling invalid provider type."""
        config = {
            "provider": "invalid"
        }
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            LLMProviderFactory.create(config)


class TestLLMManager:
    """Test LLM manager."""

    @pytest.fixture
    def manager(self):
        """Create an LLM manager instance."""
        return LLMManager({
            "provider": "ollama",
            "host": "localhost",
            "port": 11434,
            "model": "llama3",
            "timeout": 30
        })

    def test_initialization(self, manager):
        """Test manager initialization."""
        assert manager.timeout == 30
        assert manager.model == "llama3"

    def test_get_provider(self, manager):
        """Test getting the provider."""
        provider = manager.get_provider()
        assert isinstance(provider, OllamaProvider)

    @patch.object(OllamaProvider, 'list_models')
    def test_check_connection(self, mock_list, manager):
        """Test checking connection."""
        mock_list.return_value = ["llama3", "mistral"]
        is_connected, models = manager.check_connection()
        assert is_connected is True
        assert "llama3" in models


if __name__ == "__main__":
    pytest.main([__file__, "-v"])