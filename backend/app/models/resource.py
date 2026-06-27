"""Resource model — YouTube videos / playlists, PDFs, articles, notes."""
from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import ResourceKind
from app.models.mixins import TimestampMixin, UUIDPK


class Resource(Base, UUIDPK, TimestampMixin):
    __tablename__ = "resources"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=True, index=True
    )
    kind: Mapped[ResourceKind] = mapped_column(
        Enum(ResourceKind, name="resource_kind"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="resources")
    goal = relationship("Goal", back_populates="resources")