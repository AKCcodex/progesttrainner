"""YouTube Data API v3 client.

Used for playlists + video metadata. Transcripts come from a separate client
(youtube-transcript-api + yt-dlp fallback) — Data API has no transcript endpoint.

Set ``YOUTUBE_API_KEY`` to enable; otherwise the client is a no-op and only
URL-based metadata inference is available.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

from app.core.config import settings
from app.core.logging import get_logger


log = get_logger(__name__)


_VIDEO_ID_RE = re.compile(r"(?:v=|/)([0-9A-Za-z_-]{11})(?:[?&#]|$)")
_PLAYLIST_ID_RE = re.compile(r"[?&]list=([0-9A-Za-z_-]+)")


def extract_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    if "youtu.be" in host:
        return parsed.path.lstrip("/")[:11] or None
    if "youtube.com" in host or "youtube-nocookie.com" in host:
        # Shorts
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2][:11] or None
        m = _VIDEO_ID_RE.search(parsed.query + "&" + parsed.path)
        if m:
            return m.group(1)
        qs = parse_qs(parsed.query)
        if qs.get("v"):
            return qs["v"][0][:11]
    return None


def extract_playlist_id(url: str) -> str | None:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if qs.get("list"):
        return qs["list"][0]
    m = _PLAYLIST_ID_RE.search(parsed.query)
    return m.group(1) if m else None


class YouTubeDataAPI:
    BASE = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: str | None = None, timeout: float = 15.0) -> None:
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        self._client = httpx.AsyncClient(timeout=timeout)
        self.enabled = bool(self.api_key)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("YOUTUBE_API_KEY not configured")
        params = {**params, "key": self.api_key}
        resp = await self._client.get(f"{self.BASE}{path}", params=params)
        resp.raise_for_status()
        return resp.json()

    async def video_metadata(self, video_id: str) -> dict[str, Any]:
        data = await self._get(
            "/videos",
            {"part": "snippet,contentDetails", "id": video_id},
        )
        items = data.get("items", [])
        if not items:
            raise LookupError(f"video {video_id} not found")
        item = items[0]
        snippet = item.get("snippet", {})
        content = item.get("contentDetails", {})
        return {
            "video_id": video_id,
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "published_at": snippet.get("publishedAt", ""),
            "duration": content.get("duration", ""),
            "description": snippet.get("description", ""),
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        }

    async def playlist_items(self, playlist_id: str, max_results: int = 50) -> list[dict[str, Any]]:
        """Return a flat list of video metadata for the playlist."""
        data = await self._get(
            "/playlistItems",
            {
                "part": "snippet,contentDetails",
                "playlistId": playlist_id,
                "maxResults": min(max_results, 50),
            },
        )
        out: list[dict[str, Any]] = []
        for item in data.get("items", []):
            video_id = item.get("contentDetails", {}).get("videoId")
            if not video_id:
                continue
            snippet = item.get("snippet", {})
            out.append(
                {
                    "video_id": video_id,
                    "title": snippet.get("title", ""),
                    "channel": snippet.get("videoOwnerChannelTitle") or snippet.get("channelTitle", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                    "position": item.get("snippet", {}).get("position", 0),
                }
            )
        return out