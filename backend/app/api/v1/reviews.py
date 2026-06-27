"""Reviews router."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.database.session import get_db
from app.models.enums import ReviewStatus
from app.schemas.lesson import ReviewOut
from app.services.review_service import ReviewService


router = APIRouter(prefix="/reviews", tags=["reviews"])


def _svc(db: Session = Depends(get_db)) -> ReviewService:
    return ReviewService(db)


@router.get("", response_model=list[ReviewOut])
def list_reviews(
    from_dt: datetime | None = Query(default=None, alias="from"),
    to_dt: datetime | None = Query(default=None, alias="to"),
    status_filter: ReviewStatus | None = Query(default=None, alias="status"),
    current: CurrentUser = ...,  # type: ignore[assignment]
    svc: ReviewService = Depends(_svc),
) -> list[ReviewOut]:
    reviews = svc.list_for_user(current.id, from_dt=from_dt, to_dt=to_dt, status=status_filter)
    return [ReviewOut.model_validate(r) for r in reviews]


@router.post("/{review_id}/complete", response_model=ReviewOut)
def complete_review(
    review_id: uuid.UUID,
    current: CurrentUser,
    svc: ReviewService = Depends(_svc),
) -> ReviewOut:
    try:
        r = svc.complete(current.id, review_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return ReviewOut.model_validate(r)