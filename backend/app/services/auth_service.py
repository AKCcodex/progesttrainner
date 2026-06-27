"""Auth service — registration + login."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginIn, RegisterIn, UserOut


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def register(self, payload: RegisterIn) -> tuple[User, str]:
        if self.repo.get_by_email(payload.email):
            raise ValueError("email already registered")
        user = User(
            email=payload.email.lower(),
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            timezone=payload.timezone,
        )
        self.repo.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user, create_access_token(str(user.id))

    def login(self, payload: LoginIn) -> tuple[User, str]:
        user = self.repo.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise ValueError("invalid email or password")
        if not user.is_active:
            raise ValueError("account is inactive")
        return user, create_access_token(str(user.id))

    def to_user_out(self, user: User) -> UserOut:
        return UserOut.model_validate(user)