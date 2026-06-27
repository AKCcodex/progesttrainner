"""Bot-facing read endpoints.

The Telegram bot process needs a subset of the API to render goals,
lessons, reviews, and dashboard stats. These endpoints accept the internal
service token (set in ``INTERNAL_BOT_TOKEN``) instead of a user JWT.
"""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import InternalBot, get_user_repo
from app.database.session import get_db
from app.models.enums import GoalStatus, LessonStatus, ReviewStatus
from app.models.goal import Goal
from app.models.lesson import Lesson
from app.models.review import Review
from app.repositories.user_repo import UserRepository
from app.services.dashboard_service import DashboardService


router = APIRouter(prefix="/internal/bot", tags=["internal-bot"])


@router.get("/users/{chat_id}/context")
def user_context(
    chat_id: str,
    _: bool = Depends(InternalBot),
    repo: UserRepository = Depends(get_user_repo),
) -> dict:
    user = repo.get_by_telegram_chat_id(chat_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not linked")
    return {
        "user_id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "timezone": user.timezone,
    }


@router.get("/users/{chat_id}/goals")
def list_goals(
    chat_id: str,
    _: bool = Depends(InternalBot),
    repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
) -> list[dict]:
    user = repo.get_by_telegram_chat_id(chat_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not linked")
    goals = list(
        db.scalars(
            select(Goal).where(Goal.user_id == user.id, Goal.status == GoalStatus.active)
        )
    )
    return [
        {"id": str(g.id), "title": g.title, "daily_minutes": g.daily_minutes}
        for g in goals
    ]


@router.get("/users/{chat_id}/today")
def today(
    goal_id: str,
    chat_id: str,
    _: bool = Depends(InternalBot),
    repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
) -> dict:
    user = repo.get_by_telegram_chat_id(chat_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not linked")
    try:
        gid = uuid.UUID(goal_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid goal_id")
    lessons = list(
        db.scalars(
            select(Lesson).where(
                Lesson.goal_id == gid,
                Lesson.user_id == user.id,
                Lesson.scheduled_for == date.today(),
            )
        )
    )
    return {
        "lessons": [
            {
                "id": str(lesson.id),
                "title": lesson.title,
                "description": lesson.description,
                "duration_minutes": lesson.duration_minutes,
                "status": lesson.status.value,
            }
            for lesson in lessons
        ]
    }


@router.get("/users/{chat_id}/dashboard")
def dashboard(
    chat_id: str,
    _: bool = Depends(InternalBot),
    repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
) -> dict:
    user = repo.get_by_telegram_chat_id(chat_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not linked")
    svc = DashboardService(db)
    return svc.build(user.id).model_dump(mode="json")


@router.post("/users/{chat_id}/lessons/{lesson_id}/complete")
def complete_lesson_for(
    chat_id: str,
    lesson_id: str,
    _: bool = Depends(InternalBot),
    repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
) -> dict:
    user = repo.get_by_telegram_chat_id(chat_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not linked")
    try:
        lid = uuid.UUID(lesson_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid lesson_id")
    lesson = db.get(Lesson, lid)
    if lesson is None or lesson.user_id != user.id:
        raise HTTPException(status_code=404, detail="lesson not found")
    from datetime import datetime, timezone

    lesson.status = LessonStatus.done
    lesson.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}


@router.post("/users/{chat_id}/reviews/{review_id}/complete")
def complete_review_for(
    chat_id: str,
    review_id: str,
    _: bool = Depends(InternalBot),
    repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
) -> dict:
    user = repo.get_by_telegram_chat_id(chat_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not linked")
    try:
        rid = uuid.UUID(review_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid review_id")
    review = db.get(Review, rid)
    if review is None or review.user_id != user.id:
        raise HTTPException(status_code=404, detail="review not found")
    from datetime import datetime, timezone

    review.status = ReviewStatus.done
    review.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}