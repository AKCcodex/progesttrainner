"""Dashboard router."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.database.session import get_db
from app.schemas.dashboard import DashboardOut
from app.services.dashboard_service import DashboardService


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _svc(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


@router.get("", response_model=DashboardOut)
def dashboard(current: CurrentUser, svc: DashboardService = Depends(_svc)) -> DashboardOut:
    return svc.build(current.id)