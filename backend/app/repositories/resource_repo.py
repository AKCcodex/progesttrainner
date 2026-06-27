"""Resource repository."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ResourceKind
from app.models.resource import Resource


class ResourceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, resource_id: uuid.UUID) -> Resource | None:
        return self.db.get(Resource, resource_id)

    def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        goal_id: uuid.UUID | None = None,
        kind: ResourceKind | None = None,
    ) -> list[Resource]:
        stmt = select(Resource).where(Resource.user_id == user_id)
        if goal_id is not None:
            stmt = stmt.where(Resource.goal_id == goal_id)
        if kind is not None:
            stmt = stmt.where(Resource.kind == kind)
        stmt = stmt.order_by(Resource.created_at.desc())
        return list(self.db.scalars(stmt))

    def add(self, resource: Resource) -> Resource:
        self.db.add(resource)
        self.db.flush()
        return resource

    def delete(self, resource: Resource) -> None:
        self.db.delete(resource)

    def commit(self) -> None:
        self.db.commit()