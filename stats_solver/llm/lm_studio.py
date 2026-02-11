"""LM Studio LLM provider implementation."""

import json
import logging
from typing import Any
import httpx

from .base import LLMProvider, LLMConfig, LLMResponse

logger = logging.getLogger(__name__)


class LMStudioProvider(LLMProvider):
    """LM Studio LLM provider implementation."""

    # LM Studio uses OpenAI-compatible API format
    def __init__(self, config: LLMConfig) -> None:
        """Initialize LM Studio provider."""
        super().__init__(config)
        self._http_client: httpx.AsyncClient | None = None

    @property
    def is_available(self) -> bool:
        """Check if LM Studio service is available."""
        return self._http_client is not None

    async def connect(self) -> bool:
        """Establish connection to LM Studio service."""
        try:
            timeout = httpx.Timeout(self.config.timeout)
            self._http_client = httpx.AsyncClient(
                base_url=self._get_endpoint(),
                timeout=timeout,
            )

            # Test connection
            models = await self.list_models()
            logger.info(f"Connected to LM Studio, found {len(models)} models")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to LM Studio: {e}")
            return False

    async def disconnect(self) -> None:
        """Close connection to LM Studio service."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
            logger.info("Disconnected from LM Studio")

    async def list_models(self) -> list[str]:
        """List available LM Studio models."""
        if not self._http_client:
            raise RuntimeError("Not connected to LM Studio")

        try:
            response = await self._http_client.get("/v1/models")
            response.raise_for_status()
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text from LM Studio using chat completion API."""
        if not self._http_client:
            raise RuntimeError("Not connected to LM Studio")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self._send_chat_request(
            messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate JSON response from LM Studio."""
        # Add JSON formatting instruction to system prompt
        json_instruction = "You must respond with valid JSON only. Do not include any explanation or markdown formatting."

        if system_prompt:
            system_prompt = f"{system_prompt}\n\n{json_instruction}"
        else:
            system_prompt = json_instruction

        response = await self.generate(prompt, system_prompt=system_prompt, **kwargs)

        try:
            # Extract JSON from response (handle potential markdown code blocks)
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response content: {response.content}")
            raise ValueError(f"LLM did not return valid JSON: {e}")

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response from chat messages using LM Studio."""
        return await self._send_chat_request(
            messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )

    async def _send_chat_request(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send chat completion request to LM Studio."""
        if not self._http_client:
            raise RuntimeError("Not connected to LM Studio")

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "top_p": self.config.top_p,
        }

        if self.config.top_k:
            payload["top_k"] = self.config.top_k

        try:
            response = await self._http_client.post("/v1/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})

            return LLMResponse(
                content=message.get("content", ""),
                model=data.get("model", self.config.model),
                provider="lm_studio",
                finish_reason=choice.get("finish_reason"),
                tokens_used=data.get("usage", {}).get("total_tokens"),
                metadata={
                    "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
                },
            )
        except Exception as e:
            logger.error(f"Failed to send chat request to LM Studio: {e}")
            raise
