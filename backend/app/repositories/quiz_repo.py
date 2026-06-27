"""Quiz + QuizAttempt repositories."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.quiz import Quiz, QuizAttempt


class QuizRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, quiz_id: uuid.UUID) -> Quiz | None:
        return self.db.get(Quiz, quiz_id)

    def list_for_goal(self, goal_id: uuid.UUID) -> list[Quiz]:
        return list(
            self.db.scalars(
                select(Quiz).where(Quiz.goal_id == goal_id).order_by(Quiz.created_at.desc())
            )
        )

    def list_for_lesson(self, lesson_id: uuid.UUID) -> list[Quiz]:
        return list(
            self.db.scalars(
                select(Quiz).where(Quiz.lesson_id == lesson_id).order_by(Quiz.created_at.desc())
            )
        )

    def add(self, quiz: Quiz) -> Quiz:
        self.db.add(quiz)
        self.db.flush()
        return quiz

    def commit(self) -> None:
        self.db.commit()


class QuizAttemptRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, attempt: QuizAttempt) -> QuizAttempt:
        self.db.add(attempt)
        self.db.flush()
        return attempt

    def list_for_quiz(self, quiz_id: uuid.UUID) -> list[QuizAttempt]:
        return list(
            self.db.scalars(
                select(QuizAttempt).where(QuizAttempt.quiz_id == quiz_id).order_by(QuizAttempt.submitted_at.desc())
            )
        )

    def list_for_user(self, user_id: uuid.UUID, limit: int = 100) -> list[QuizAttempt]:
        return list(
            self.db.scalars(
                select(QuizAttempt)
                .where(QuizAttempt.user_id == user_id)
                .order_by(QuizAttempt.submitted_at.desc())
                .limit(limit)
            )
        )

    def commit(self) -> None:
        self.db.commit()