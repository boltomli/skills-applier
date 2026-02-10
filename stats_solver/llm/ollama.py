"""Ollama LLM provider implementation."""

import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from .base import LLMProvider, LLMConfig, LLMResponse

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama LLM provider implementation."""
    
    def __init__(self, config: LLMConfig) -> None:
        """Initialize Ollama provider."""
        super().__init__(config)
        self._http_client: Optional[httpx.AsyncClient] = None
    
    @property
    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        return self._http_client is not None
    
    async def connect(self) -> bool:
        """Establish connection to Ollama service."""
        try:
            timeout = httpx.Timeout(self.config.timeout)
            self._http_client = httpx.AsyncClient(
                base_url=self._get_endpoint(),
                timeout=timeout,
            )
            
            # Test connection
            models = await self.list_models()
            logger.info(f"Connected to Ollama, found {len(models)} models")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Close connection to Ollama service."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
            logger.info("Disconnected from Ollama")
    
    async def list_models(self) -> List[str]:
        """List available Ollama models."""
        if not self._http_client:
            raise RuntimeError("Not connected to Ollama")
        
        try:
            response = await self._http_client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text from Ollama."""
        if not self._http_client:
            raise RuntimeError("Not connected to Ollama")
        
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": max_tokens or self.config.max_tokens,
                "top_p": self.config.top_p,
            },
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if self.config.top_k:
            payload["options"]["top_k"] = self.config.top_k
        
        try:
            response = await self._http_client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data.get("response", ""),
                model=data.get("model", self.config.model),
                provider="ollama",
                finish_reason=data.get("done_reason"),
                tokens_used=data.get("eval_count", 0) + data.get("prompt_eval_count", 0),
                metadata={
                    "prompt_eval_count": data.get("prompt_eval_count", 0),
                    "eval_count": data.get("eval_count", 0),
                },
            )
        except Exception as e:
            logger.error(f"Failed to generate from Ollama: {e}")
            raise
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate JSON response from Ollama."""
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
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response from chat messages using Ollama chat API."""
        if not self._http_client:
            raise RuntimeError("Not connected to Ollama")
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": max_tokens or self.config.max_tokens,
                "top_p": self.config.top_p,
            },
        }
        
        if self.config.top_k:
            payload["options"]["top_k"] = self.config.top_k
        
        try:
            response = await self._http_client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                model=data.get("model", self.config.model),
                provider="ollama",
                finish_reason=data.get("done_reason"),
                tokens_used=data.get("eval_count", 0) + data.get("prompt_eval_count", 0),
                metadata={
                    "prompt_eval_count": data.get("prompt_eval_count", 0),
                    "eval_count": data.get("eval_count", 0),
                },
            )
        except Exception as e:
            logger.error(f"Failed to chat with Ollama: {e}")
            raise