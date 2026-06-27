"""Auth router — register + login."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.auth import LoginIn, RegisterIn, TokenOut
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


def _service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, svc: AuthService = Depends(_service)) -> TokenOut:
    try:
        user, token = svc.register(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return TokenOut(access_token=token, user=svc.to_user_out(user))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, svc: AuthService = Depends(_service)) -> TokenOut:
    try:
        user, token = svc.login(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return TokenOut(access_token=token, user=svc.to_user_out(user))