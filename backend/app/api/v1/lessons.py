"""Lessons router."""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.database.session import get_db
from app.schemas.lesson import LessonOut
from app.schemas.quiz import QuizOut
from app.services.lesson_service import LessonService
from app.services.quiz_service import QuizService


router = APIRouter(prefix="/lessons", tags=["lessons"])


def _svc(db: Session = Depends(get_db)) -> LessonService:
    return LessonService(db)


def _quiz_svc(db: Session = Depends(get_db)) -> QuizService:
    return QuizService(db)


@router.get("", response_model=list[LessonOut])
def list_lessons(
    goal_id: uuid.UUID,
    target_date: date | None = Query(default=None, alias="date"),
    current: CurrentUser = ...,  # type: ignore[assignment]
    svc: LessonService = Depends(_svc),
) -> list[LessonOut]:
    target = target_date or date.today()
    try:
        lessons = svc.list_for_goal_on_date(current.id, goal_id, target)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return [LessonOut.model_validate(lesson) for lesson in lessons]


@router.post("/{lesson_id}/complete", response_model=LessonOut)
def complete_lesson(
    lesson_id: uuid.UUID, current: CurrentUser, svc: LessonService = Depends(_svc)
) -> LessonOut:
    try:
        lesson = svc.complete(current.id, lesson_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return LessonOut.model_validate(lesson)


@router.post("/{lesson_id}/skip", response_model=LessonOut)
def skip_lesson(
    lesson_id: uuid.UUID, current: CurrentUser, svc: LessonService = Depends(_svc)
) -> LessonOut:
    try:
        lesson = svc.skip(current.id, lesson_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return LessonOut.model_validate(lesson)


@router.post("/{lesson_id}/quiz", response_model=QuizOut, status_code=status.HTTP_201_CREATED)
async def generate_quiz_for_lesson(
    lesson_id: uuid.UUID,
    current: CurrentUser,
    lesson_svc: LessonService = Depends(_svc),
    quiz_svc: QuizService = Depends(_quiz_svc),
) -> QuizOut:
    try:
        lesson_svc.lesson_repo.get(lesson_id)  # ownership check
    except LookupError:
        raise HTTPException(status_code=404, detail="lesson not found")
    quiz = await quiz_svc.generate_for_lesson(current.id, lesson_id)
    return QuizOut.model_validate(quiz)