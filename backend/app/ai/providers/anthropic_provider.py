"""Anthropic provider — uses the official SDK in async mode."""
from __future__ import annotations

from typing import Any

from anthropic import AsyncAnthropic

from app.ai.provider import AIProvider
from app.ai.providers.base import extract_json
from app.ai.prompts import (
    SYSTEM_COACH,
    evaluate_answer_prompt,
    quiz_prompt,
    summarize_prompt,
)
from app.core.config import settings


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self) -> None:
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required when AI_PROVIDER=anthropic")
        if not settings.ANTHROPIC_MODEL:
            raise ValueError("ANTHROPIC_MODEL is required when AI_PROVIDER=anthropic")
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        resp = await self.client.messages.create(
            model=self.model,
            system=system or SYSTEM_COACH,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # content is a list of blocks
        parts = []
        for block in resp.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "".join(parts)

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

    async def aclose(self) -> None:
        await self.client.close()