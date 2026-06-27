FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir "python-telegram-bot[ext]==21.10" httpx==0.28.0

WORKDIR /app
COPY bot.py /app/bot.py

CMD ["python", "-u", "bot.py"]