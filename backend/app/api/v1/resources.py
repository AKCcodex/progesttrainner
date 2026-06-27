"""Resources router."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import CurrentUser
from app.database.session import get_db
from app.models.enums import ResourceKind
from app.schemas.resource import ResourceCreateIn, ResourceOut
from app.services.resource_service import ResourceService


router = APIRouter(prefix="/resources", tags=["resources"])


def _svc(db: Session = Depends(get_db)) -> ResourceService:
    return ResourceService(db)


@router.post("", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
async def create_resource(
    payload: ResourceCreateIn,
    current: CurrentUser,
    svc: ResourceService = Depends(_svc),
) -> ResourceOut:
    resource = await svc.create(current, payload)
    return ResourceOut.model_validate(resource)


@router.post("/upload-pdf", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    goal_id: uuid.UUID | None = Form(default=None),
    title: str | None = Form(default=None),
    file: UploadFile = File(...),
    current: CurrentUser = ...,  # type: ignore[assignment]
    svc: ResourceService = Depends(_svc),
) -> ResourceOut:
    if file.content_type and not file.content_type.startswith("application/pdf"):
        raise HTTPException(status_code=415, detail="only PDF uploads supported")
    data_dir = Path(settings.DATA_DIR) / "pdfs" / str(current.id)
    data_dir.mkdir(parents=True, exist_ok=True)
    dest = data_dir / f"{uuid.uuid4().hex}.pdf"
    dest.write_bytes(await file.read())

    resource = ResourceService(svc.db)  # reuse session
    payload = ResourceCreateIn(
        goal_id=goal_id,
        kind=ResourceKind.pdf,
        title=title or file.filename or "uploaded.pdf",
    )
    r = await resource.create(current, payload)
    r.storage_path = str(dest)
    svc.db.commit()
    svc.db.refresh(r)
    return ResourceOut.model_validate(r)


@router.get("", response_model=list[ResourceOut])
def list_resources(
    goal_id: uuid.UUID | None = Query(default=None),
    kind: ResourceKind | None = Query(default=None),
    current: CurrentUser = ...,  # type: ignore[assignment]
    svc: ResourceService = Depends(_svc),
) -> list[ResourceOut]:
    items = svc.list_for_user(current.id, goal_id=goal_id, kind=kind)
    return [ResourceOut.model_validate(r) for r in items]


@router.get("/{resource_id}", response_model=ResourceOut)
def get_resource(
    resource_id: uuid.UUID, current: CurrentUser, svc: ResourceService = Depends(_svc)
) -> ResourceOut:
    try:
        r = svc.get(current.id, resource_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return ResourceOut.model_validate(r)


@router.post("/{resource_id}/refresh", response_model=ResourceOut)
async def refresh_resource(
    resource_id: uuid.UUID,
    current: CurrentUser,
    svc: ResourceService = Depends(_svc),
) -> ResourceOut:
    try:
        svc.get(current.id, resource_id)  # ownership check
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    await svc.enrich(str(resource_id))
    return ResourceOut.model_validate(svc.get(current.id, resource_id))


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_resource(
    resource_id: uuid.UUID, current: CurrentUser, svc: ResourceService = Depends(_svc)
) -> Response:
    try:
        svc.delete(current.id, resource_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)