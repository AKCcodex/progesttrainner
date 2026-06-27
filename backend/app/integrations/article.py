"""Article URL → main-text fetcher using trafilatura."""
from __future__ import annotations

import httpx
import trafilatura

from app.core.logging import get_logger


log = get_logger(__name__)


class ArticleFetchError(Exception):
    pass


async def fetch_article_text(url: str, *, timeout: float = 20.0) -> tuple[str, str]:
    """Return (title, text). Falls back to ('', raw_html) if extraction fails."""
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (LearningCoach)"})
        resp.raise_for_status()
        html = resp.text

    extracted = trafilatura.extract(html, include_comments=False, include_tables=False, favor_recall=True)
    title = trafilatura.extract_metadata(html).title if trafilatura.extract_metadata(html) else ""
    if extracted:
        return title or "", extracted
    log.info("trafilatura empty for %s; using raw html", url)
    return title or "", html