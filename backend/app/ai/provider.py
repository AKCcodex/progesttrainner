"""Abstract AI provider.

Implementations live in :mod:`app.ai.providers`. The factory at the bottom
selects one based on ``settings.AI_PROVIDER``. No provider hardcodes its
model — they all read it from environment variables at construction time.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger


log = get_logger(__name__)


class AIProvider(ABC):
    name: str

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Single-turn text generation."""

    @abstractmethod
    async def summarize(self, text: str, *, max_words: int = 200) -> str:
        """Return a concise summary of ``text``."""

    @abstractmethod
    async def create_quiz(
        self,
        source: str,
        *,
        n_questions: int = 5,
        kinds: list[str] | None = None,
    ) -> list[dict]:
        """Generate a quiz from ``source`` text.

        Each question dict should look like:
            {
                "id": "q1",
                "kind": "mcq" | "short_answer" | "flashcard",
                "question": "...",
                "options": ["...", "..."],       # for mcq
                "answer": "...",                # for short_answer / flashcard
                "explanation": "...",
            }
        """

    @abstractmethod
    async def evaluate_answer(
        self,
        question: str,
        reference: str,
        user_answer: str,
    ) -> dict:
        """Return ``{"score": float in [0, 1], "feedback": "..."}``."""

    # ----- shared helpers -----

    async def aclose(self) -> None:  # pragma: no cover
        return None


_singleton: AIProvider | None = None


def get_ai_provider() -> AIProvider:
    """Lazy-initialised singleton based on ``settings.AI_PROVIDER``."""
    global _singleton
    if _singleton is not None:
        return _singleton

    name = settings.AI_PROVIDER.lower()
    if name == "ollama":
        from app.ai.providers.ollama import OllamaProvider

        _singleton = OllamaProvider()
    elif name == "openai":
        from app.ai.providers.openai_provider import OpenAIProvider

        _singleton = OpenAIProvider()
    elif name == "anthropic":
        from app.ai.providers.anthropic_provider import AnthropicProvider

        _singleton = AnthropicProvider()
    elif name == "gemini":
        from app.ai.providers.gemini_provider import GeminiProvider

        _singleton = GeminiProvider()
    elif name == "openai_compatible":
        from app.ai.providers.openai_compatible import OpenAICompatibleProvider

        _singleton = OpenAICompatibleProvider()
    else:
        raise ValueError(f"unknown AI_PROVIDER: {settings.AI_PROVIDER!r}")

    log.info("initialised AI provider: %s", _singleton.name)
    return _singleton


def reset_ai_provider() -> None:
    """Test helper — drop the cached singleton."""
    global _singleton
    _singleton = None


__all__ = ["AIProvider", "get_ai_provider", "reset_ai_provider"]