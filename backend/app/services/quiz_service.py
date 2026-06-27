"""Quiz service — generation, scoring, evaluation."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from app.ai.provider import get_ai_provider
from app.core.logging import get_logger
from app.models.enums import QuizKind
from app.models.lesson import Lesson
from app.models.quiz import Quiz, QuizAttempt
from app.repositories.goal_repo import GoalRepository
from app.repositories.lesson_repo import LessonRepository
from app.repositories.quiz_repo import QuizAttemptRepository, QuizRepository
from app.repositories.resource_repo import ResourceRepository


log = get_logger(__name__)


def _normalize(s: str) -> str:
    return " ".join(s.lower().split())


def _mcq_score(question: dict, user_answer: str) -> tuple[float, str]:
    """MCQ: exact match on the option text or the option index."""
    options = question.get("options") or []
    answer = question.get("answer", "")
    # Accept either the answer text or a 0-based index.
    candidates = {answer.strip().lower()}
    try:
        idx = int(user_answer)
        if 0 <= idx < len(options):
            candidates.add(options[idx].strip().lower())
    except (ValueError, TypeError):
        pass
    candidates.add(user_answer.strip().lower())
    if any(c for c in candidates if c and c in (a.lower() for a in options)):
        return 1.0, "Correct."
    return 0.0, f"Expected: {answer}"


def _short_answer_score(question: dict, user_answer: str) -> tuple[float, str]:
    """Quick heuristic: token-overlap + SequenceMatcher. AI fallback if confidence is low."""
    reference = _normalize(question.get("answer", ""))
    user = _normalize(user_answer)
    if not reference:
        return 0.0, "No reference answer available."
    ratio = SequenceMatcher(None, reference, user).ratio()
    # Token overlap
    ref_tokens = set(reference.split())
    user_tokens = set(user.split())
    overlap = len(ref_tokens & user_tokens) / max(1, len(ref_tokens))
    score = max(ratio, overlap)
    if score >= 0.7:
        return score, "Good — covered the key points."
    # AI evaluation for harder cases.
    return -1.0, ""  # sentinel → caller will use AI


class QuizService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = QuizRepository(db)
        self.attempt_repo = QuizAttemptRepository(db)
        self.lesson_repo = LessonRepository(db)
        self.goal_repo = GoalRepository(db)
        self.resource_repo = ResourceRepository(db)

    async def generate_for_lesson(
        self,
        user_id: uuid.UUID,
        lesson_id: uuid.UUID,
        *,
        n_questions: int = 5,
        kinds: list[str] | None = None,
    ) -> Quiz:
        lesson = self.lesson_repo.get(lesson_id)
        if lesson is None or lesson.user_id != user_id:
            raise LookupError("lesson not found")
        source_text = self._gather_source_text(lesson)
        provider = get_ai_provider()
        questions = await provider.create_quiz(source_text, n_questions=n_questions, kinds=kinds or ["mcq", "short_answer"])
        quiz = Quiz(
            goal_id=lesson.goal_id,
            lesson_id=lesson.id,
            user_id=user_id,
            kind=QuizKind.mixed,
            title=f"Quiz: {lesson.title}",
            questions=questions,
        )
        self.repo.add(quiz)
        self.db.commit()
        self.db.refresh(quiz)
        return quiz

    def _gather_source_text(self, lesson: Lesson) -> str:
        parts: list[str] = []
        if lesson.description:
            parts.append(lesson.description)
        for rid in lesson.source_resource_ids or []:
            try:
                r = self.resource_repo.get(uuid.UUID(str(rid)))
            except (ValueError, TypeError):
                continue
            if r is None:
                continue
            if r.transcript:
                parts.append(f"Resource: {r.title}\n{r.transcript[:4000]}")
            elif r.content_text:
                parts.append(f"Resource: {r.title}\n{r.content_text[:4000]}")
        return "\n\n".join(parts) or f"Topic: {lesson.title}"

    async def submit(self, user_id: uuid.UUID, quiz_id: uuid.UUID, answers: list[dict]) -> QuizAttempt:
        quiz = self.repo.get(quiz_id)
        if quiz is None or quiz.user_id != user_id:
            raise LookupError("quiz not found")

        answer_map = {str(a.get("question_id")): a.get("answer", "") for a in answers}
        per_question: list[dict] = []
        total = 0.0
        ai_provider = get_ai_provider()

        for q in quiz.questions or []:
            qid = str(q.get("id"))
            user_ans = str(answer_map.get(qid, ""))
            kind = q.get("kind", "mcq")
            score, feedback = 0.0, ""
            if kind == "mcq":
                score, feedback = _mcq_score(q, user_ans)
            elif kind == "short_answer":
                score, feedback = _short_answer_score(q, user_ans)
                if score < 0:
                    # delegate to AI
                    try:
                        eval_result = await ai_provider.evaluate_answer(
                            q.get("question", ""), q.get("answer", ""), user_ans
                        )
                        score = float(eval_result.get("score", 0.0))
                        feedback = str(eval_result.get("feedback", ""))
                    except Exception as exc:
                        log.warning("AI evaluation failed: %s", exc)
                        score, feedback = 0.0, "Could not evaluate answer."
            else:  # flashcard
                score = 1.0 if user_ans.strip() else 0.0
                feedback = "Recorded." if score else "Skipped."
            per_question.append(
                {
                    "question_id": qid,
                    "kind": kind,
                    "score": score,
                    "feedback": feedback,
                    "user_answer": user_ans,
                }
            )
            total += score

        n = max(1, len(quiz.questions or []))
        attempt = QuizAttempt(
            quiz_id=quiz.id,
            user_id=user_id,
            answers=per_question,
            score=total / n,
            feedback={"per_question": per_question},
            submitted_at=datetime.now(timezone.utc),
        )
        self.attempt_repo.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt