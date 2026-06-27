"""Internal AI smoke-test endpoint. Lets operators verify the provider wiring
without going through the full lesson-generation flow.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.ai.provider import get_ai_provider
from app.core.config import settings
from app.core.deps import CurrentUser


router = APIRouter(prefix="/internal/ai", tags=["internal-ai"])


@router.get("/status")
def status(_: CurrentUser) -> dict:
    return {
        "provider": settings.AI_PROVIDER,
        "model": {
            "ollama": settings.OLLAMA_MODEL,
            "openai": settings.OPENAI_MODEL,
            "anthropic": settings.ANTHROPIC_MODEL,
            "gemini": settings.GEMINI_MODEL,
            "openai_compatible": settings.OPENAI_COMPAT_MODEL,
        }.get(settings.AI_PROVIDER, ""),
    }


@router.post("/test")
async def ai_test(payload: dict, _: CurrentUser) -> dict:
    prompt = payload.get("prompt", "Say hello in one short sentence.")
    try:
        provider = get_ai_provider()
        text = await provider.generate(prompt, system="You are a helpful assistant.")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider error: {exc}")
    return {"provider": provider.name, "text": text}