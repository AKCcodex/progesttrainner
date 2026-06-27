"""High-level YouTube client — combines Data API + transcripts."""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.integrations.youtube.data_api import YouTubeDataAPI, extract_playlist_id, extract_video_id
from app.integrations.youtube.transcripts import fetch_transcript


log = get_logger(__name__)


class YouTubeClient:
    def __init__(self) -> None:
        self.data_api = YouTubeDataAPI()

    async def aclose(self) -> None:
        await self.data_api.aclose()

    async def expand_video(self, url: str) -> dict[str, Any]:
        """Return metadata + transcript for a single video URL."""
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError(f"could not extract video id from {url!r}")
        meta: dict[str, Any] = {
            "video_id": video_id,
            "url": url,
            "title": "",
            "channel": "",
            "duration": "",
            "thumbnail": "",
        }
        if self.data_api.enabled:
            try:
                data = await self.data_api.video_metadata(video_id)
                meta.update(data)
            except Exception as exc:
                log.warning("YouTube Data API failed for %s: %s", video_id, exc)
        transcript = fetch_transcript(video_id)
        if transcript:
            meta["transcript"] = transcript
        return meta

    async def expand_playlist(self, url: str) -> dict[str, Any]:
        """Return playlist-level metadata + a list of video entries (transcript optional)."""
        playlist_id = extract_playlist_id(url)
        if not playlist_id:
            raise ValueError(f"could not extract playlist id from {url!r}")
        out: dict[str, Any] = {
            "playlist_id": playlist_id,
            "url": url,
            "title": "",
            "video_count": 0,
            "videos": [],
        }
        if not self.data_api.enabled:
            raise RuntimeError(
                "YOUTUBE_API_KEY not configured — playlist expansion requires it. "
                "Set the env var or add videos individually."
            )
        videos = await self.data_api.playlist_items(playlist_id)
        out["video_count"] = len(videos)
        out["videos"] = videos
        out["title"] = playlist_id  # Data API needs another call for the playlist title; keep id for now.
        return out