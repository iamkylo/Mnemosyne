"""
providers/huggingface.py

Provider adapter for Hugging Face Inference API.

Supports:
  - Text generation via the HF Inference API (serverless).
  - Embeddings via the feature-extraction endpoint.

Docs: https://huggingface.co/docs/api-inference/index
"""

from __future__ import annotations

import httpx

from core.config import settings
from core.constants import HTTP_CLIENT_TIMEOUT
from providers.base import ProviderAdapter


_HF_BASE_URL = "https://api-inference.huggingface.co/models"
_DEFAULT_CHAT_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
_DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class HuggingFaceProvider(ProviderAdapter):
    """
    Hugging Face Inference API adapter.

    ``api_key`` should be a HuggingFace Access Token (hf_...).
    """

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        super().__init__(
            endpoint=endpoint or _HF_BASE_URL,
            api_key=api_key or settings.hf_token,
            metadata=metadata or {},
        )
        self._chat_model: str = str(
            self.metadata.get("chat_model", _DEFAULT_CHAT_MODEL)
        )
        self._embed_model: str = str(
            self.metadata.get("embed_model", _DEFAULT_EMBED_MODEL)
        )
        self._timeout = int(self.metadata.get("timeout", HTTP_CLIENT_TIMEOUT))

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def complete(self, prompt: str) -> str:
        """Call the HF text-generation endpoint and extract the generated text."""
        url = f"{self.endpoint}/{self._chat_model}"
        body = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.2,
                "return_full_text": False,
            },
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=body, headers=self._headers())
            response.raise_for_status()
            data = response.json()
            # HF returns a list of generation objects
            if isinstance(data, list) and data:
                return data[0].get("generated_text", "")
            return ""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Call the HF feature-extraction endpoint to get dense embeddings."""
        url = f"{self.endpoint}/{self._embed_model}"
        body = {"inputs": texts, "options": {"wait_for_model": True}}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=body, headers=self._headers())
            response.raise_for_status()
            data = response.json()
            # Response is either [[float]] or [[[float]]] depending on model
            if data and isinstance(data[0][0], list):
                # Take the CLS token representation (index 0) for each input
                return [item[0] for item in data]
            return data
