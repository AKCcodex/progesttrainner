"""Convenience import — make ``app.models`` a single import surface for Alembic."""
from app.models.user import User  # noqa: F401
from app.models.goal import Goal  # noqa: F401
from app.models.resource import Resource  # noqa: F401
from app.models.lesson import Lesson  # noqa: F401
from app.models.review import Review  # noqa: F401
from app.models.quiz import Quiz, QuizAttempt  # noqa: F401
from app.models.notification import Notification  # noqa: F401