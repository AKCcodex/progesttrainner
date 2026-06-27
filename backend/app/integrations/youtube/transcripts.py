"""Transcript extraction.

Tries ``youtube-transcript-api`` first. If it fails (e.g. captions disabled,
region-locked) falls back to ``yt-dlp`` subtitle download.
"""
from __future__ import annotations

import json
import os
import tempfile
from typing import Any

from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
from youtube_transcript_api._errors import (  # type: ignore
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from app.core.logging import get_logger


log = get_logger(__name__)


class TranscriptError(Exception):
    """No transcript could be extracted for the given video."""


def _format_segments(segments: list[Any]) -> str:
    """Convert either FetchedTranscriptSnippet objects or dicts into plain text."""
    parts: list[str] = []
    for seg in segments:
        if isinstance(seg, dict):
            text = seg.get("text", "")
        else:
            text = getattr(seg, "text", "")
        text = (text or "").replace("\n", " ").strip()
        if text:
            parts.append(text)
    return " ".join(parts)


def fetch_transcript_api(video_id: str, languages: list[str] | None = None) -> str | None:
    """Try to fetch a transcript via youtube-transcript-api."""
    try:
        langs = languages or ["en"]
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=langs)
        return _format_segments(fetched)
    except (TranscriptsDisabled, VideoUnavailable, NoTranscriptFound) as exc:
        log.info("transcript-api miss for %s: %s", video_id, exc)
        return None
    except Exception as exc:  # pragma: no cover — defensive
        log.warning("transcript-api unexpected error for %s: %s", video_id, exc)
        return None


def fetch_transcript_ytdlp(video_id: str) -> str | None:
    """Last-resort: download auto-generated subtitles via yt-dlp."""
    try:
        import yt_dlp  # type: ignore

        opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en.*", "en"],
            "subtitlesformat": "vtt",
            "outtmpl": os.path.join(tempfile.gettempdir(), "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            subs = info.get("requested_subtitles") or info.get("subtitles") or {}
            if not subs:
                return None
            lang = next(iter(subs.keys()))
            with tempfile.TemporaryDirectory() as tmp:
                opts["outtmpl"] = os.path.join(tmp, "%(id)s.%(ext)s")
                with yt_dlp.YoutubeDL(opts) as ydl2:
                    ydl2.download([f"https://www.youtube.com/watch?v={video_id}"])
                # Find the resulting vtt file
                for fname in os.listdir(tmp):
                    if fname.endswith(f".{lang}.vtt"):
                        with open(os.path.join(tmp, fname), encoding="utf-8", errors="ignore") as fh:
                            return _vtt_to_text(fh.read())
        return None
    except Exception as exc:  # pragma: no cover
        log.warning("yt-dlp transcript fallback failed for %s: %s", video_id, exc)
        return None


def _vtt_to_text(vtt: str) -> str:
    """Strip VTT timestamps / styling; return plain text."""
    lines: list[str] = []
    for raw in vtt.splitlines():
        line = raw.strip()
        if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
            continue
        if "-->" in line:
            continue
        # Strip HTML-ish tags (<c>, <00:00:00.000>)
        import re

        line = re.sub(r"<[^>]+>", "", line)
        if line:
            lines.append(line)
    return " ".join(lines)


def fetch_transcript(video_id: str) -> str | None:
    """Try multiple sources. Returns the first non-empty transcript or None."""
    transcript = fetch_transcript_api(video_id)
    if transcript:
        return transcript
    log.info("falling back to yt-dlp for %s", video_id)
    return fetch_transcript_ytdlp(video_id)


__all__ = [
    "fetch_transcript",
    "fetch_transcript_api",
    "fetch_transcript_ytdlp",
    "TranscriptError",
]  # noqa: WPS410