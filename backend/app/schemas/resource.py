"""Resource schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ResourceKind


class ResourceCreateIn(BaseModel):
    goal_id: Optional[uuid.UUID] = None
    kind: ResourceKind
    title: Optional[str] = None
    url: Optional[str] = None
    text: Optional[str] = Field(
        default=None, description="Used for kind=note. Inline body of the note."
    )


class ResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    goal_id: Optional[uuid.UUID]
    kind: ResourceKind
    title: str
    url: Optional[str]
    storage_path: Optional[str]
    meta: dict
    transcript: Optional[str]
    content_text: Optional[str]
    created_at: datetime