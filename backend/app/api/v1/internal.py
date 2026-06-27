"""Internal endpoints used by the Telegram bot process."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import InternalBot
from app.schemas.auth import TelegramLinkCodeOut
from app.services.user_service import UserService


router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/telegram/ping", dependencies=[Depends(InternalBot)])
def ping() -> dict[str, str]:
    """Liveness probe used by the bot to confirm the service token works."""
    return {"status": "ok"}


@router.post(
    "/telegram/redeem-link-code",
    response_model=TelegramLinkCodeOut,
    dependencies=[Depends(InternalBot)],
)
def redeem_link_code(payload: dict, svc: UserService = Depends()) -> TelegramLinkCodeOut:  # noqa: B008
    from app.database.session import SessionLocal

    code = payload.get("code")
    chat_id = payload.get("chat_id")
    if not code or not chat_id:
        raise HTTPException(status_code=422, detail="code and chat_id are required")

    db = SessionLocal()
    try:
        service = UserService(db)
        try:
            user = service.link_telegram_chat(code=code, chat_id=chat_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        # After linking, issue a fresh code for a future re-link if needed.
        code, expires_at = service.issue_telegram_link_code(user)
        return TelegramLinkCodeOut(code=code, expires_at=expires_at)
    finally:
        db.close()