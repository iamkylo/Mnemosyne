"""
providers/groq.py

Provider adapter for Groq Cloud LLM API.

Groq supports chat completions and native embeddings (using models like nomic-embed-text-v1_5).

Docs: https://console.groq.com/docs/openai
"""

from __future__ import annotations

import httpx

from core.config import settings
from core.constants import HTTP_CLIENT_TIMEOUT
from providers.base import ProviderAdapter


_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_DEFAULT_CHAT_MODEL = "llama3-70b-8192"
_DEFAULT_EMBED_MODEL = "nomic-embed-text-v1_5"


class GroqProvider(ProviderAdapter):
    """
    Groq Cloud adapter.

    Implements:
      - ``complete(prompt)``  — single-turn chat completion.
      - ``embed(texts)``      — returns embeddings using Groq API.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        super().__init__(
            endpoint=endpoint or _GROQ_BASE_URL,
            api_key=api_key or settings.groq_api_key,
            metadata=metadata or {},
        )
        self._chat_model: str = str(
            self.metadata.get("chat_model", _DEFAULT_CHAT_MODEL)
        )
        self._timeout = int(self.metadata.get("timeout", HTTP_CLIENT_TIMEOUT))

    async def complete(self, prompt: str) -> str:
        """Send a chat completion request to Groq and return the response text."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._chat_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 2048,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self.endpoint}/chat/completions",
                json=body,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings using Groq's native embedding model.
        """
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "input": texts,
            "model": _DEFAULT_EMBED_MODEL,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self.endpoint}/embeddings",
                json=body,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]
