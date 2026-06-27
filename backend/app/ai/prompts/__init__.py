"""Shared prompt templates. Kept as plain string constants so they're easy
to inspect and unit-test.
"""
from __future__ import annotations

SYSTEM_COACH = (
    "You are a disciplined personal learning coach. You design study plans, "
    "summarise material, generate practice questions, and evaluate answers "
    "honestly. Be concise, specific, and actionable. Output only what is asked for."
)


def roadmap_prompt(goal_title: str, goal_description: str | None, daily_minutes: int,
                   resources_summary: str) -> str:
    desc = f"\nGoal description: {goal_description}" if goal_description else ""
    return (
        f"Create a learning roadmap for the goal below.\n\n"
        f"Goal: {goal_title}{desc}\n"
        f"Daily study time available: {daily_minutes} minutes\n"
        f"Available resources:\n{resources_summary}\n\n"
        "Return STRICT JSON in this exact shape (no prose outside the JSON):\n"
        "{\n"
        '  "weeks": [\n'
        '    {"week": 1, "theme": "...", "objectives": ["...", "..."]}\n'
        "  ],\n"
        '  "milestones": ["...", "..."]\n'
        "}"
    )


def daily_lesson_prompt(
    goal_title: str,
    daily_minutes: int,
    resources_summary: str,
    scheduled_for: str,
    prior_lessons: str,
) -> str:
    return (
        f"Plan today's study session for the learner.\n\n"
        f"Goal: {goal_title}\n"
        f"Date: {scheduled_for}\n"
        f"Daily time budget: {daily_minutes} minutes\n"
        f"Resources available:\n{resources_summary}\n"
        f"Recent lessons already taught (so we don't repeat):\n{prior_lessons or 'None yet.'}\n\n"
        "Return STRICT JSON, no prose outside the JSON:\n"
        "{\n"
        '  "lessons": [\n'
        '    {"title": "...", "description": "...", "duration_minutes": 20, "focus_resource_title": "..."}\n'
        "  ]\n"
        "}\n"
        f"Provide between 1 and {max(1, daily_minutes // 15)} lessons that fit within {daily_minutes} minutes."
    )


def quiz_prompt(source: str, n_questions: int, kinds: list[str]) -> str:
    return (
        "Generate a quiz that tests understanding of the source material below.\n\n"
        f"Source:\n\"\"\"\n{source[:6000]}\n\"\"\"\n\n"
        f"Number of questions: {n_questions}\n"
        f"Allowed question kinds: {', '.join(kinds)}\n\n"
        "Return STRICT JSON, no prose outside the JSON:\n"
        "{\n"
        '  "questions": [\n'
        '    {\n'
        '      "id": "q1",\n'
        '      "kind": "mcq" | "short_answer" | "flashcard",\n'
        '      "question": "...",\n'
        '      "options": ["A", "B", "C", "D"],\n'
        '      "answer": "B",\n'
        '      "explanation": "..."\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "For mcq include exactly 4 options and set answer to the correct option text.\n"
        "For short_answer set answer to a 1-2 sentence reference answer.\n"
        "For flashcard set answer to a brief back-of-card explanation."
    )


def evaluate_answer_prompt(question: str, reference: str, user_answer: str) -> str:
    return (
        "Score the learner's answer against the reference.\n\n"
        f"Question: {question}\n"
        f"Reference answer: {reference}\n"
        f"Learner's answer: {user_answer}\n\n"
        "Return STRICT JSON:\n"
        '{\n  "score": 0.0..1.0,\n  "feedback": "one short paragraph"\n}'
    )


def summarize_prompt(text: str, max_words: int) -> str:
    return (
        f"Summarise the following content in at most {max_words} words. "
        "Preserve key concepts and any actionable steps.\n\n"
        f"Content:\n\"\"\"\n{text[:6000]}\n\"\"\""
    )