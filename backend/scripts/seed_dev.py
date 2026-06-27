"""Seed a demo user + a sample goal + resources for local exploration.

Usage (from the backend directory):

    docker compose exec backend python -m scripts.seed_dev

Or outside Docker:

    cd backend && python -m scripts.seed_dev
"""
from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.enums import GoalStatus, ResourceKind
from app.models.goal import Goal
from app.models.resource import Resource
from app.models.user import User
from app.services.lesson_service import LessonService


DEMO_EMAIL = "demo@coach.local"
DEMO_PASSWORD = "demopassword123"
DEMO_NAME = "Demo Learner"


async def seed() -> None:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(
                email=DEMO_EMAIL,
                hashed_password=hash_password(DEMO_PASSWORD),
                full_name=DEMO_NAME,
                timezone="UTC",
            )
            db.add(user)
            db.flush()
            print(f"[seed] created user {user.email} (id={user.id})")
        else:
            print(f"[seed] user {user.email} already exists")

        goal = db.scalar(select(Goal).where(Goal.user_id == user.id, Goal.title == "Learn Rust"))
        if goal is None:
            goal = Goal(
                user_id=user.id,
                title="Learn Rust",
                description="Build a small CLI app with structs, errors, and async.",
                daily_minutes=30,
                status=GoalStatus.active,
            )
            db.add(goal)
            db.flush()
            print(f"[seed] created goal {goal.title} (id={goal.id})")

        if not db.scalars(select(Resource).where(Resource.goal_id == goal.id)).first():
            db.add(
                Resource(
                    user_id=user.id,
                    goal_id=goal.id,
                    kind=ResourceKind.note,
                    title="Rust book — chapter 3 notes",
                    content_text=(
                        "Rust ownership rules: each value has an owner, there can only be one owner at a time, "
                        "and when the owner goes out of scope the value is dropped. Borrowing allows references "
                        "without taking ownership; the compiler enforces that either one mutable reference or any "
                        "number of immutable references exist at a time. Lifetimes tie references to their scopes "
                        "and prevent dangling references. Lifetimes are inferred most of the time, but may need to "
                        "be declared explicitly in function signatures."
                    ),
                    meta={"source": "seed_dev.py"},
                )
            )
            db.flush()
            print("[seed] added a sample note resource")

        db.commit()

        # Generate today's lessons immediately so the demo lands populated.
        n = await LessonService(db).generate_today_for_all_users()
        print(f"[seed] generated {n} lessons across all goals")
    finally:
        db.close()


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()