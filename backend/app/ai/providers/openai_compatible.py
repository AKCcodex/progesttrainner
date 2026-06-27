"""OpenAI-compatible provider — any chat endpoint that speaks the /v1/chat shape.

Works with LM Studio, vLLM, llama.cpp server, OpenRouter, etc.
"""
from __future__ import annotations

from typing import Any

import httpx

from app.ai.provider import AIProvider
from app.ai.providers.base import extract_json
from app.ai.prompts import (
    SYSTEM_COACH,
    evaluate_answer_prompt,
    quiz_prompt,
    summarize_prompt,
)
from app.core.config import settings


class OpenAICompatibleProvider(AIProvider):
    name = "openai_compatible"

    def __init__(self, timeout: float = 120.0) -> None:
        if not settings.OPENAI_COMPAT_BASE_URL:
            raise ValueError("OPENAI_COMPAT_BASE_URL is required when AI_PROVIDER=openai_compatible")
        if not settings.OPENAI_COMPAT_MODEL:
            raise ValueError("OPENAI_COMPAT_MODEL is required when AI_PROVIDER=openai_compatible")
        self.base_url = settings.OPENAI_COMPAT_BASE_URL.rstrip("/")
        self.api_key = settings.OPENAI_COMPAT_API_KEY or "no-key"
        self.model = settings.OPENAI_COMPAT_MODEL
        self._client = httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = await self._client.post(
            f"{self.base_url}/chat/completions", headers=self._headers(), json=payload
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def _generate_json(self, prompt: str, system: str | None = None) -> Any:
        text = await self.generate(prompt, system=system or SYSTEM_COACH, temperature=0.4, max_tokens=1500)
        return extract_json(text)

    async def summarize(self, text: str, *, max_words: int = 200) -> str:
        return await self.generate(summarize_prompt(text, max_words), system=SYSTEM_COACH, temperature=0.3)

    async def create_quiz(
        self, source: str, *, n_questions: int = 5, kinds: list[str] | None = None
    ) -> list[dict]:
        kinds = kinds or ["mcq", "short_answer", "flashcard"]
        data = await self._generate_json(quiz_prompt(source, n_questions, kinds))
        questions = data.get("questions", []) if isinstance(data, dict) else []
        out = []
        for i, q in enumerate(questions, start=1):
            if isinstance(q, dict):
                q.setdefault("id", f"q{i}")
                out.append(q)
        return out

    async def evaluate_answer(self, question: str, reference: str, user_answer: str) -> dict:
        data = await self._generate_json(evaluate_answer_prompt(question, reference, user_answer))
        if not isinstance(data, dict):
            return {"score": 0.0, "feedback": str(data)}
        score = float(data.get("score", 0.0))
        return {"score": max(0.0, min(1.0, score)), "feedback": str(data.get("feedback", ""))}