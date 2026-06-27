# Personal AI Learning Coach

A production-ready personal learning coach. You supply goals + resources; the system produces a daily plan, quizzes you on the material, schedules spaced repetition reviews, and adapts to your pace. Notifications default to Telegram.

## Highlights

- **Pluggable AI** — Ollama (default), OpenAI, Anthropic, Gemini, or any OpenAI-compatible endpoint. Switch via `AI_PROVIDER` env var. No model names are hardcoded.
- **Resource ingestion** — YouTube videos + playlists, PDFs (with text extraction), article URLs, manual notes.
- **Adaptive pacing** — completion rate and quiz scores drive nightly adjustments to your daily time budget.
- **Spaced repetition** — automatic 1 / 3 / 7 / 14 / 30-day review chain on every completed lesson.
- **Telegram bot** — `/start`, `/goal`, `/resources`, `/today`, `/progress`, plus inline keyboards for marking lessons complete.
- **JWT auth**, **PostgreSQL + Alembic**, **Redis + RQ**, **APScheduler**, **Docker Compose**.

## Architecture

```
┌────────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│  Next.js Frontend  │───▶│   FastAPI Backend    │───▶│  PostgreSQL DB  │
└────────────────────┘    │  (Python 3.12)       │    └─────────────────┘
        ▲                 │  ┌────────────────┐  │    ┌─────────────────┐
        │ JWT             │  │ AI Provider    │──┼───▶│  Redis + RQ     │
┌────────────────────┐    │  │ Abstraction    │  │    └─────────────────┘
│ Telegram User      │◀───┼──│ APScheduler    │  │    ┌─────────────────┐
└────────────────────┘    │  └────────────────┘  │───▶│ Telegram bot    │
                          └──────────────────────┘    └─────────────────┘
                          (Docker Compose orchestrates everything)
```

## Quickstart

```bash
git clone <this-repo>
cd trainer
cp .env.example .env
# fill in OLLAMA_*, TELEGRAM_BOT_TOKEN, YOUTUBE_API_KEY at minimum
docker compose up -d --build
```

When the stack is up:

```bash
curl http://localhost:8000/health
# → {"status":"ok"}

# register and log in via the web UI at http://localhost:3000
```

See [`docs/LOCAL_DEV.md`](docs/LOCAL_DEV.md) for the full setup walkthrough, including running the backend outside Docker for development.

## Switching AI providers

Set `AI_PROVIDER` to one of: `ollama`, `openai`, `anthropic`, `gemini`, `openai_compatible`. Provide the matching credentials and model env var:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Then restart the backend. The Ollama default works against both Ollama Cloud (set `OLLAMA_API_KEY`) and a local server (`OLLAMA_BASE_URL=http://host.docker.internal:11434`).

## Endpoints (v1)

| Method | Path | Notes |
|--------|------|-------|
| `POST` | `/api/v1/auth/register` | email + password + full_name → JWT |
| `POST` | `/api/v1/auth/login` | → JWT |
| `GET`  | `/api/v1/users/me` | current user |
| `POST` | `/api/v1/goals` | create |
| `GET`  | `/api/v1/goals` | list |
| `GET/PATCH/DELETE` | `/api/v1/goals/{id}` | detail / update / archive |
| `POST` | `/api/v1/resources` | JSON body — URL or note text |
| `POST` | `/api/v1/resources/upload-pdf` | multipart PDF |
| `GET`  | `/api/v1/resources` | list |
| `GET`  | `/api/v1/lessons?goal_id=…&date=…` | daily plan |
| `POST` | `/api/v1/lessons/{id}/complete` | mark done; triggers review chain |
| `POST` | `/api/v1/lessons/{id}/quiz` | generate AI quiz |
| `POST` | `/api/v1/quizzes/{id}/submit` | score answers |
| `GET`  | `/api/v1/reviews?from=…&to=…` | review list |
| `POST` | `/api/v1/reviews/{id}/complete` | mark done |
| `GET`  | `/api/v1/dashboard` | streak, completion %, study hours, per-goal progress |

Internal bot endpoints (require `INTERNAL_BOT_TOKEN`):

| Method | Path | Notes |
|--------|------|-------|
| `POST` | `/api/v1/internal/telegram/redeem-link-code` | link chat_id to user |
| `GET`  | `/api/v1/internal/bot/users/{chat_id}/goals` | active goals |
| `GET`  | `/api/v1/internal/bot/users/{chat_id}/today` | today's plan |
| `GET`  | `/api/v1/internal/bot/users/{chat_id}/dashboard` | stats |
| `POST` | `/api/v1/internal/bot/users/{chat_id}/lessons/{id}/complete` | mark done |

## Telegram bot

1. Talk to [@BotFather](https://t.me/BotFather) and create a bot. Copy the token to `TELEGRAM_BOT_TOKEN`.
2. In the web app, click "Generate Telegram link code" on your profile.
3. In Telegram, send `/link <code>` to the bot.
4. Use `/today` to see today's lessons with one-tap "Done" buttons.

## Project layout

```
app/                     # backend (FastAPI)
├── core/                # config, security, logging, deps
├── database/            # SQLAlchemy base + session + Redis
├── models/              # ORM models + enums
├── schemas/             # pydantic request/response models
├── repositories/        # thin data-access layer
├── services/            # business logic
├── ai/                  # provider abstraction + 5 implementations
├── api/v1/              # HTTP routers
├── scheduler/           # APScheduler jobs + runner
├── notifications/       # channel ABC + Telegram + email stub
├── integrations/        # YouTube, PDF, article fetchers
└── workers/             # RQ tasks + worker entrypoint
bot/                     # python-telegram-bot process
frontend/                # Next.js + Tailwind
migrations/              # Alembic
docs/                    # local dev guide
```

## License

MIT.