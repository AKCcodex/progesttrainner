"""Ollama provider — default.

Works with both the Ollama Cloud API (Bearer-auth) and a local Ollama server
(no auth). Uses the OpenAI-compatible ``/v1/chat/completions`` endpoint when
``OLLAMA_BASE_URL`` exposes it (cloud does); falls back to ``/api/chat``
otherwise.
"""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.ai.provider import AIProvider
from app.ai.prompts import (
    SYSTEM_COACH,
    evaluate_answer_prompt,
    quiz_prompt,
    summarize_prompt,
)
from app.core.config import settings
from app.core.logging import get_logger


log = get_logger(__name__)


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self, timeout: float = 120.0) -> None:
        if not settings.OLLAMA_MODEL:
            raise ValueError("OLLAMA_MODEL is required when AI_PROVIDER=ollama")
        if not settings.OLLAMA_BASE_URL:
            raise ValueError("OLLAMA_BASE_URL is required when AI_PROVIDER=ollama")
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.api_key = settings.OLLAMA_API_KEY
        self.model = settings.OLLAMA_MODEL
        self._client = httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    def _auth_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

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

        # Prefer the OpenAI-compatible chat endpoint, which Ollama Cloud
        # exposes and which local Ollama also serves at /v1.
        for path in ("/v1/chat/completions", "/api/chat"):
            url = f"{self.base_url}{path}"
            payload = (
                {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
                if path.startswith("/v1")
                else {"model": self.model, "messages": messages, "stream": False, "options": {"temperature": temperature}}
            )
            try:
                resp = await self._client.post(url, headers=self._auth_headers(), json=payload)
                if resp.status_code == 404:
                    continue  # try next path
                resp.raise_for_status()
                data = resp.json()
                if path.startswith("/v1"):
                    return data["choices"][0]["message"]["content"]
                return data.get("message", {}).get("content", "")
            except httpx.HTTPError as exc:
                log.warning("Ollama call to %s failed: %s", url, exc)
                if path == "/api/chat":
                    raise
                continue
        raise RuntimeError("could not reach Ollama on /v1/chat/completions or /api/chat")

    # ----- structured helpers -----

    @staticmethod
    def _extract_json(text: str) -> Any:
        """Pull the first JSON object/array out of a possibly chatty response."""
        # Strip markdown code fences if present
        fenced = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
        if fenced:
            return json.loads(fenced.group(1))
        # Greedy first JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise ValueError(f"could not parse JSON from model output: {text[:200]!r}")

    async def _generate_json(self, prompt: str, system: str | None = None) -> Any:
        text = await self.generate(prompt, system=system or SYSTEM_COACH, temperature=0.4, max_tokens=1500)
        return self._extract_json(text)

    async def summarize(self, text: str, *, max_words: int = 200) -> str:
        prompt = summarize_prompt(text, max_words)
        return await self.generate(prompt, system=SYSTEM_COACH, temperature=0.3, max_tokens=600)

    async def create_quiz(
        self,
        source: str,
        *,
        n_questions: int = 5,
        kinds: list[str] | None = None,
    ) -> list[dict]:
        kinds = kinds or ["mcq", "short_answer", "flashcard"]
        prompt = quiz_prompt(source, n_questions, kinds)
        data = await self._generate_json(prompt)
        questions = data.get("questions", []) if isinstance(data, dict) else []
        out: list[dict] = []
        for i, q in enumerate(questions, start=1):
            if not isinstance(q, dict):
                continue
            q.setdefault("id", f"q{i}")
            out.append(q)
        return out

    async def evaluate_answer(
        self, question: str, reference: str, user_answer: str
    ) -> dict:
        prompt = evaluate_answer_prompt(question, reference, user_answer)
        data = await self._generate_json(prompt)
        if not isinstance(data, dict):
            return {"score": 0.0, "feedback": str(data)}
        score = float(data.get("score", 0.0))
        return {"score": max(0.0, min(1.0, score)), "feedback": str(data.get("feedback", ""))}