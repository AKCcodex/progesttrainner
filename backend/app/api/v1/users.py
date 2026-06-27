"""User router — profile + Telegram linking."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.database.session import get_db
from app.schemas.auth import TelegramLinkCodeOut, UserOut, UserUpdateIn
from app.services.user_service import UserService


router = APIRouter(prefix="/users", tags=["users"])


def _svc(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("/me", response_model=UserOut)
def me(current: CurrentUser) -> UserOut:
    return UserOut.model_validate(current)


@router.patch("/me", response_model=UserOut)
def update_me(payload: UserUpdateIn, current: CurrentUser, svc: UserService = Depends(_svc)) -> UserOut:
    svc.update_profile(current, payload)
    return UserOut.model_validate(current)


@router.post("/me/telegram-link-code", response_model=TelegramLinkCodeOut)
def issue_telegram_link_code(current: CurrentUser, svc: UserService = Depends(_svc)) -> TelegramLinkCodeOut:
    code, expires_at = svc.issue_telegram_link_code(current)
    return TelegramLinkCodeOut(code=code, expires_at=expires_at)