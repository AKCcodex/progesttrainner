"""FastAPI dependencies — DB session, current user, service token."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization.split(" ", 1)[1].strip()


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    repo: UserRepository = Depends(get_user_repo),
) -> User:
    token = _extract_bearer(authorization)
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("token missing sub")
        user = repo.get(uuid.UUID(user_id))
    except (ValueError, Exception) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid credentials: {exc}",
        ) from exc
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found or inactive")
    return user


def require_internal_bot_token(
    authorization: Annotated[str | None, Header()] = None,
    x_internal_token: Annotated[str | None, Header()] = None,
) -> bool:
    """Authorize the standalone Telegram bot process on internal endpoints."""
    expected = settings.INTERNAL_BOT_TOKEN
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="bot token not configured")
    presented = x_internal_token or _extract_bearer(authorization)
    if presented != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return True


CurrentUser = Annotated[User, Depends(get_current_user)]
InternalBot = Annotated[bool, Depends(require_internal_bot_token)]