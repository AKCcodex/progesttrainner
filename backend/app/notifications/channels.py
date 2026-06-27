"""Notification channel abstraction.

Concrete channels live in their own modules. The :func:`notify_user` helper
selects the best channel for a given user and persists the result.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.enums import NotificationChannel, NotificationStatus
from app.models.notification import Notification
from app.models.user import User


log = get_logger(__name__)


class NotificationChannelBase(ABC):
    name: NotificationChannel

    @abstractmethod
    async def send(self, user: User, payload: dict[str, Any]) -> bool: ...


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def notify_user(db: Session, user: User, payload: dict[str, Any]) -> Notification:
    """Pick a channel and persist a Notification row regardless of outcome."""
    channel_name = NotificationChannel.telegram if user.telegram_chat_id else NotificationChannel.email
    record = Notification(
        user_id=user.id,
        channel=channel_name,
        payload=payload,
        status=NotificationStatus.queued,
        created_at=_utcnow(),
    )
    db.add(record)

    if channel_name == NotificationChannel.telegram:
        if not user.telegram_chat_id:
            record.status = NotificationStatus.failed
            record.error = "user has no telegram_chat_id linked"
            db.commit()
            return record
        from app.notifications.telegram_channel import TelegramChannel

        channel = TelegramChannel()
    else:
        from app.notifications.email_channel import EmailChannel

        channel = EmailChannel()

    try:
        ok = await channel.send(user, payload)
        record.status = NotificationStatus.sent if ok else NotificationStatus.failed
        if ok:
            record.sent_at = _utcnow()
        else:
            record.error = "channel returned False"
    except NotImplementedError as exc:
        record.status = NotificationStatus.failed
        record.error = str(exc)
        log.warning("notification channel %s not implemented: %s", channel_name, exc)
    except Exception as exc:
        record.status = NotificationStatus.failed
        record.error = f"{exc.__class__.__name__}: {exc}"
        log.exception("notification send failed for user %s", user.id)

    db.commit()
    db.refresh(record)
    return record