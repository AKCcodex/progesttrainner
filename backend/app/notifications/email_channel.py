"""Email channel — stub.

A future implementation would wire SMTP / SES / Postmark here. The abstract
contract is stable, so adding a new channel is a single-file change.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.models.enums import NotificationChannel
from app.models.user import User
from app.notifications.channels import NotificationChannelBase


log = get_logger(__name__)


class EmailChannel(NotificationChannelBase):
    name = NotificationChannel.email

    async def send(self, user: User, payload: dict[str, Any]) -> bool:
        # TODO: implement SMTP / SES / Postmark wiring. The interface is
        # stable; persistence and user-channel routing are already in place.
        raise NotImplementedError(
            "EmailChannel.send is not implemented in this build. "
            "Add SMTP credentials and a transport in this file to enable."
        )