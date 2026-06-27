"""Resource service — ingest + enrichment orchestration."""
from __future__ import annotations

import asyncio
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.integrations.article import fetch_article_text
from app.integrations.pdf.extractor import extract_pdf_text
from app.integrations.youtube.client import YouTubeClient
from app.models.enums import ResourceKind
from app.models.resource import Resource
from app.models.user import User
from app.repositories.resource_repo import ResourceRepository
from app.schemas.resource import ResourceCreateIn
from app.workers.tasks import enqueue_resource_enrichment


log = get_logger(__name__)


class ResourceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ResourceRepository(db)

    async def create(self, user: User, payload: ResourceCreateIn) -> Resource:
        resource = Resource(
            user_id=user.id,
            goal_id=payload.goal_id,
            kind=payload.kind,
            title=payload.title or payload.url or (payload.text or "")[:60],
            url=payload.url,
            meta={},
        )
        if payload.kind == ResourceKind.note and payload.text:
            resource.content_text = payload.text
        self.repo.add(resource)
        self.db.commit()
        self.db.refresh(resource)

        # Fire-and-forget enrichment. If the queue is unavailable we still succeed
        # because the user can hit /resources/{id}/refresh later.
        try:
            enqueue_resource_enrichment(str(resource.id))
        except Exception as exc:  # pragma: no cover — Redis down
            log.warning("could not enqueue enrichment for resource %s: %s", resource.id, exc)
        return resource

    async def enrich(self, resource_id: str) -> None:
        """Pull remote content (transcript / PDF / article) into the resource row."""
        try:
            rid = uuid.UUID(resource_id)
        except ValueError:
            log.warning("invalid resource id %s", resource_id)
            return

        resource = self.repo.get(rid)
        if resource is None:
            log.warning("resource %s disappeared before enrichment", rid)
            return

        try:
            if resource.kind in (ResourceKind.youtube_video,):
                await self._enrich_youtube_video(resource)
            elif resource.kind == ResourceKind.youtube_playlist:
                await self._enrich_youtube_playlist(resource)
            elif resource.kind == ResourceKind.pdf and resource.storage_path:
                await self._enrich_pdf(resource)
            elif resource.kind == ResourceKind.article and resource.url:
                await self._enrich_article(resource)
            elif resource.kind == ResourceKind.note:
                pass  # already stored at create-time
        except Exception as exc:
            log.exception("enrichment failed for resource %s: %s", rid, exc)
            resource.meta = {**(resource.meta or {}), "enrichment_error": str(exc)}
        finally:
            self.db.commit()

    async def _enrich_youtube_video(self, resource: Resource) -> None:
        assert resource.url
        client = YouTubeClient()
        try:
            data = await client.expand_video(resource.url)
        finally:
            await client.aclose()
        resource.title = data.get("title") or resource.title
        resource.transcript = data.get("transcript")
        resource.meta = {
            **(resource.meta or {}),
            "video_id": data.get("video_id"),
            "channel": data.get("channel"),
            "duration": data.get("duration"),
            "thumbnail": data.get("thumbnail"),
        }

    async def _enrich_youtube_playlist(self, resource: Resource) -> None:
        assert resource.url
        client = YouTubeClient()
        try:
            data = await client.expand_playlist(resource.url)
        finally:
            await client.aclose()
        resource.title = data.get("title") or resource.title
        resource.meta = {
            **(resource.meta or {}),
            "playlist_id": data.get("playlist_id"),
            "video_count": data.get("video_count"),
            "videos": data.get("videos"),
        }

    async def _enrich_pdf(self, resource: Resource) -> None:
        assert resource.storage_path
        from pathlib import Path

        path = Path(resource.storage_path)
        data = path.read_bytes()
        text = extract_pdf_text(data)
        resource.content_text = text
        resource.meta = {**(resource.meta or {}), "bytes": len(data), "char_count": len(text)}

    async def _enrich_article(self, resource: Resource) -> None:
        assert resource.url
        title, text = await fetch_article_text(resource.url)
        if title and not resource.title:
            resource.title = title
        resource.content_text = text
        resource.meta = {**(resource.meta or {}), "char_count": len(text)}

    def list_for_user(
        self, user_id: uuid.UUID, *, goal_id: uuid.UUID | None = None, kind: ResourceKind | None = None
    ) -> list[Resource]:
        return self.repo.list_for_user(user_id, goal_id=goal_id, kind=kind)

    def get(self, user_id: uuid.UUID, resource_id: uuid.UUID) -> Resource:
        r = self.repo.get(resource_id)
        if r is None or r.user_id != user_id:
            raise LookupError("resource not found")
        return r

    def delete(self, user_id: uuid.UUID, resource_id: uuid.UUID) -> None:
        r = self.get(user_id, resource_id)
        self.repo.delete(r)
        self.db.commit()