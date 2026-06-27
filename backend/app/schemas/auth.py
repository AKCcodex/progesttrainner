"""Auth + user schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=120)
    timezone: str = Field(default="UTC", max_length=64)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    timezone: str
    telegram_chat_id: str | None
    created_at: datetime


class UserUpdateIn(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    timezone: str | None = Field(default=None, max_length=64)


class TelegramLinkCodeOut(BaseModel):
    code: str
    expires_at: datetime


TokenOut.model_rebuild()