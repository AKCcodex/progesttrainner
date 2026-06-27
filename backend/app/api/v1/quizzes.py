"""Quizzes router."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.database.session import get_db
from app.schemas.quiz import QuizAttemptOut, QuizOut, QuizSubmissionIn
from app.services.quiz_service import QuizService


router = APIRouter(prefix="/quizzes", tags=["quizzes"])


def _svc(db: Session = Depends(get_db)) -> QuizService:
    return QuizService(db)


@router.get("/{quiz_id}", response_model=QuizOut)
def get_quiz(quiz_id: uuid.UUID, current: CurrentUser, svc: QuizService = Depends(_svc)) -> QuizOut:
    from app.repositories.quiz_repo import QuizRepository

    repo = QuizRepository(svc.db)
    q = repo.get(quiz_id)
    if q is None or q.user_id != current.id:
        raise HTTPException(status_code=404, detail="quiz not found")
    return QuizOut.model_validate(q)


@router.post("/{quiz_id}/submit", response_model=QuizAttemptOut)
async def submit_quiz(
    quiz_id: uuid.UUID,
    payload: QuizSubmissionIn,
    current: CurrentUser,
    svc: QuizService = Depends(_svc),
) -> QuizAttemptOut:
    try:
        attempt = await svc.submit(current.id, quiz_id, payload.answers)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return QuizAttemptOut.model_validate(attempt)