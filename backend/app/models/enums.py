"""Enums used across models."""
from __future__ import annotations

import enum


class GoalStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    completed = "completed"
    archived = "archived"


class ResourceKind(str, enum.Enum):
    youtube_video = "youtube_video"
    youtube_playlist = "youtube_playlist"
    pdf = "pdf"
    article = "article"
    note = "note"


class LessonStatus(str, enum.Enum):
    pending = "pending"
    done = "done"
    skipped = "skipped"


class ReviewStatus(str, enum.Enum):
    pending = "pending"
    done = "done"
    missed = "missed"


class QuizKind(str, enum.Enum):
    mcq = "mcq"
    short_answer = "short_answer"
    flashcard = "flashcard"
    mixed = "mixed"


class NotificationChannel(str, enum.Enum):
    telegram = "telegram"
    email = "email"


class NotificationStatus(str, enum.Enum):
    queued = "queued"
    sent = "sent"
    failed = "failed"