"""Personal AI Learning Coach — Telegram bot.

Standalone process. Speaks to the FastAPI backend over HTTP using the
INTERNAL_BOT_TOKEN service token.

Commands:
    /start               welcome + onboarding
    /link <code>         link chat to user (after frontend /me/telegram-link-code)
    /goal                list active goals; choose one
    /resources           resource counts per goal
    /today               today's plan for the active goal
    /progress            dashboard stats
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)


BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://backend:8000").rstrip("/")
INTERNAL_BOT_TOKEN = os.environ.get("INTERNAL_BOT_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

logging.basicConfig(
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("coach-bot")


class Backend:
    """Thin HTTP client for the bot process."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=BACKEND_BASE_URL,
            headers={"Authorization": f"Bearer {INTERNAL_BOT_TOKEN}"},
            timeout=15.0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def redeem_link_code(self, code: str, chat_id: str) -> dict[str, Any]:
        r = await self._client.post(
            "/api/v1/internal/telegram/redeem-link-code",
            json={"code": code, "chat_id": chat_id},
        )
        r.raise_for_status()
        return r.json()

    async def context(self, chat_id: str) -> dict[str, Any] | None:
        try:
            r = await self._client.get(f"/api/v1/internal/bot/users/{chat_id}/context")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise
        r.raise_for_status()
        return r.json()

    async def goals(self, chat_id: str) -> list[dict[str, Any]]:
        r = await self._client.get(f"/api/v1/internal/bot/users/{chat_id}/goals")
        r.raise_for_status()
        return r.json()

    async def today(self, chat_id: str, goal_id: str) -> dict[str, Any]:
        r = await self._client.get(
            f"/api/v1/internal/bot/users/{chat_id}/today",
            params={"goal_id": goal_id},
        )
        r.raise_for_status()
        return r.json()

    async def dashboard(self, chat_id: str) -> dict[str, Any]:
        r = await self._client.get(f"/api/v1/internal/bot/users/{chat_id}/dashboard")
        r.raise_for_status()
        return r.json()

    async def complete_lesson(self, chat_id: str, lesson_id: str) -> None:
        r = await self._client.post(
            f"/api/v1/internal/bot/users/{chat_id}/lessons/{lesson_id}/complete"
        )
        r.raise_for_status()

    async def complete_review(self, chat_id: str, review_id: str) -> None:
        r = await self._client.post(
            f"/api/v1/internal/bot/users/{chat_id}/reviews/{review_id}/complete"
        )
        r.raise_for_status()


backend = Backend()


# ----- commands -----


async def cmd_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    ctx = await backend.context(str(chat_id))
    if ctx is None:
        await update.message.reply_text(
            "👋 Welcome! Your Telegram isn't linked yet.\n\n"
            "1) Register or log in to the Learning Coach web app.\n"
            "2) Go to your profile and click 'Generate Telegram link code'.\n"
            "3) Send the code back here with /link <code>."
        )
        return
    await update.message.reply_text(
        f"👋 Welcome back, {ctx.get('full_name') or ctx.get('email')}!\n"
        "Type /today to see today's plan, /progress for stats, or /goal to switch goals."
    )


async def cmd_link(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    args = (update.message.text or "").split()
    if len(args) != 2:
        await update.message.reply_text("Usage: /link <6-character-code>")
        return
    code = args[1].strip().upper()
    try:
        result = await backend.redeem_link_code(code, str(chat_id))
    except httpx.HTTPStatusError as exc:
        await update.message.reply_text(
            f"❌ Could not link: {exc.response.json().get('detail', exc.response.text[:200])}"
        )
        return
    await update.message.reply_text(
        "✅ Linked! Type /today to see today's plan."
    )


async def cmd_goal(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    try:
        goals = await backend.goals(chat_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            await update.message.reply_text(
                "Your Telegram isn't linked yet. Send /start for instructions."
            )
            return
        raise
    if not goals:
        await update.message.reply_text("You have no active goals yet. Create one in the web app.")
        return
    keyboard = [
        [InlineKeyboardButton(g["title"], callback_data=f"goal:{g['id']}")]
        for g in goals
    ]
    await update.message.reply_text(
        "Choose a goal:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def callback_goal_pick(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    goal_id = query.data.split(":", 1)[1]
    chat_id = str(query.message.chat.id)
    data = await backend.today(chat_id, goal_id)
    lessons = data.get("lessons", [])
    if not lessons:
        await query.edit_message_text("📭 No lessons scheduled for today.")
        return
    lines = ["📚 Today's plan:\n"]
    keyboard: list[list[InlineKeyboardButton]] = []
    for l in lessons:
        lines.append(f"• {l['title']} ({l['duration_minutes']}m)")
        if l["status"] == "pending":
            keyboard.append(
                [InlineKeyboardButton(f"✅ Done — {l['title'][:30]}", callback_data=f"done:{l['id']}")]
            )
    await query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard))


async def callback_done(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    lesson_id = query.data.split(":", 1)[1]
    chat_id = str(query.message.chat.id)
    try:
        await backend.complete_lesson(chat_id, lesson_id)
    except httpx.HTTPStatusError as exc:
        await query.answer(f"Could not mark done: {exc.response.status_code}", show_alert=True)
        return
    await query.edit_message_text("✅ Marked complete. Nice work!")


async def cmd_resources(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    # Lightweight: just show today's lesson count per goal.
    chat_id = str(update.effective_chat.id)
    try:
        goals = await backend.goals(chat_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            await update.message.reply_text("Your Telegram isn't linked yet. /start")
            return
        raise
    if not goals:
        await update.message.reply_text("No active goals. Add one in the web app.")
        return
    lines = ["📦 Active goals:"]
    for g in goals:
        try:
            today = await backend.today(chat_id, g["id"])
            n = len(today.get("lessons", []))
        except Exception:
            n = 0
        lines.append(f"• {g['title']} — today: {n} lesson(s), daily budget {g['daily_minutes']}m")
    await update.message.reply_text("\n".join(lines))


async def cmd_today(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    try:
        goals = await backend.goals(chat_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            await update.message.reply_text("Your Telegram isn't linked yet. /start")
            return
        raise
    if not goals:
        await update.message.reply_text("No active goals yet.")
        return
    goal = goals[0]
    data = await backend.today(chat_id, goal["id"])
    lessons = data.get("lessons", [])
    if not lessons:
        await update.message.reply_text(
            f"📭 No lessons scheduled today for '{goal['title']}'. "
            f"Check back tomorrow or generate one via the web app."
        )
        return
    lines = [f"📚 Today's plan — {goal['title']}:\n"]
    keyboard: list[list[InlineKeyboardButton]] = []
    for l in lessons:
        lines.append(f"• {l['title']} ({l['duration_minutes']}m)")
        if l["status"] == "pending":
            keyboard.append(
                [InlineKeyboardButton(f"✅ Done — {l['title'][:30]}", callback_data=f"done:{l['id']}")]
            )
    await update.message.reply_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_progress(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    try:
        d = await backend.dashboard(chat_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            await update.message.reply_text("Your Telegram isn't linked yet. /start")
            return
        raise
    msg = (
        f"📊 Progress\n"
        f"• Streak: {d['current_streak_days']} days\n"
        f"• Completion (30d): {int(d['completion_pct_30d'] * 100)}%\n"
        f"• Lessons done (total): {d['lessons_completed_total']}\n"
        f"• Study hours (30d): {d['study_hours_30d']}\n"
        f"• Quiz average: {int(d['quiz_average_pct'] * 100)}%"
    )
    await update.message.reply_text(msg)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        log.warning(
            "TELEGRAM_BOT_TOKEN is not set — bot is disabled. "
            "Set TELEGRAM_BOT_TOKEN in .env and restart the bot container to enable it."
        )
        # Keep the container alive (don't crash-loop) so other services
        # aren't affected. The bot simply does nothing.
        import signal
        stop = {"v": False}

        def _shutdown(*_a):
            stop["v"] = True

        signal.signal(signal.SIGTERM, _shutdown)
        signal.signal(signal.SIGINT, _shutdown)
        while not stop["v"]:
            import time as _t
            _t.sleep(1)
        return
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("link", cmd_link))
    app.add_handler(CommandHandler("goal", cmd_goal))
    app.add_handler(CommandHandler("resources", cmd_resources))
    app.add_handler(CommandHandler("today", cmd_today))
    app.add_handler(CommandHandler("progress", cmd_progress))
    app.add_handler(CallbackQueryHandler(callback_goal_pick, pattern=r"^goal:"))
    app.add_handler(CallbackQueryHandler(callback_done, pattern=r"^done:"))

    log.info("bot starting; backend=%s", BACKEND_BASE_URL)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()