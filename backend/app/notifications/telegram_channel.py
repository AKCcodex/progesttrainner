"""Telegram channel — uses the official Bot HTTP API directly via httpx.

Avoids pulling in the full python-telegram-bot package on the backend side
(it's installed in the bot container).
"""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.models.enums import NotificationChannel
from app.models.user import User
from app.notifications.channels import NotificationChannelBase


log = get_logger(__name__)


class TelegramChannel(NotificationChannelBase):
    name = NotificationChannel.telegram

    def __init__(self, timeout: float = 10.0) -> None:
        self.token = settings.TELEGRAM_BOT_TOKEN
        self._client = httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def send(self, user: User, payload: dict[str, Any]) -> bool:
        if not self.token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN not configured")
        if not user.telegram_chat_id:
            log.warning("user %s has no telegram_chat_id", user.id)
            return False

        text = payload.get("text") or ""
        if not text:
            log.info("empty telegram payload, skipping")
            return True

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        body = {
            "chat_id": user.telegram_chat_id,
            "text": text[:3900],
            "disable_web_page_preview": True,
        }
        if payload.get("parse_mode") == "markdown":
            body["parse_mode"] = "MarkdownV2"

        resp = await self._client.post(url, json=body)
        if resp.status_code >= 400:
            log.warning(
                "telegram send failed (%s): %s", resp.status_code, resp.text[:300]
            )
            return False
        return True