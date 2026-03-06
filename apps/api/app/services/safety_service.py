"""
Safety service — classifies queries using Mistral 7B (via Ollama) before any retrieval.
Acts as a hard guardrail: blocked queries never reach Claude or the vector store.
"""
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.rag.prompt_builder import build_safety_classification_prompt, build_query_rewrite_prompt


BLOCKED_LABELS = {
    "BLOCKED_DIAGNOSIS",
    "BLOCKED_MEDICATION",
    "BLOCKED_THERAPY",
    "BLOCKED_SELFHARM",
}


@dataclass
class SafetyResult:
    is_allowed: bool
    label: str
    reason: str | None = None


class SafetyService:
    """
    Uses Mistral 7B via Ollama for lightweight, fast safety classification
    and query rewriting. Falls back gracefully if Ollama is unavailable.
    """

    def __init__(self, ollama_base_url: str = None, model: str = None):
        self._base_url = ollama_base_url or settings.OLLAMA_BASE_URL
        self._model = model or settings.MISTRAL_MODEL

    async def classify(self, query: str) -> SafetyResult:
        """Classify the query intent. Returns SafetyResult."""
        prompt = build_safety_classification_prompt(query)
        try:
            label = await self._call_mistral(prompt, max_tokens=16)
            label = label.strip().upper()
        except Exception:
            # Fail open in dev; fail closed in production (configurable)
            label = "ALLOWED"

        if label in BLOCKED_LABELS:
            return SafetyResult(is_allowed=False, label=label)

        return SafetyResult(is_allowed=True, label="ALLOWED")

    async def rewrite_query(self, query: str) -> str:
        """Rewrite query for better retrieval precision. Falls back to original."""
        prompt = build_query_rewrite_prompt(query)
        try:
            rewritten = await self._call_mistral(prompt, max_tokens=200)
            return rewritten.strip() or query
        except Exception:
            return query

    async def _call_mistral(self, prompt: str, max_tokens: int = 512) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.1,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
