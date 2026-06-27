"""Goals router."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.database.session import get_db
from app.models.enums import GoalStatus
from app.schemas.goal import GoalCreateIn, GoalOut, GoalUpdateIn
from app.services.goal_service import GoalService


router = APIRouter(prefix="/goals", tags=["goals"])


def _svc(db: Session = Depends(get_db)) -> GoalService:
    return GoalService(db)


@router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(payload: GoalCreateIn, current: CurrentUser, svc: GoalService = Depends(_svc)) -> GoalOut:
    goal = svc.create(
        current.id,
        title=payload.title,
        description=payload.description,
        daily_minutes=payload.daily_minutes,
        target_date=payload.target_date,
    )
    return GoalOut.model_validate(goal)


@router.get("", response_model=list[GoalOut])
def list_goals(
    current: CurrentUser,
    svc: GoalService = Depends(_svc),
    status_filter: GoalStatus | None = Query(default=None, alias="status"),
) -> list[GoalOut]:
    goals = svc.list_for_user(current.id, status=status_filter)
    return [GoalOut.model_validate(g) for g in goals]


@router.get("/{goal_id}", response_model=GoalOut)
def get_goal(goal_id: uuid.UUID, current: CurrentUser, svc: GoalService = Depends(_svc)) -> GoalOut:
    try:
        goal = svc.get(current.id, goal_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return GoalOut.model_validate(goal)


@router.patch("/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: uuid.UUID, payload: GoalUpdateIn, current: CurrentUser, svc: GoalService = Depends(_svc)
) -> GoalOut:
    try:
        goal = svc.update(current.id, goal_id, **payload.model_dump(exclude_unset=True))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return GoalOut.model_validate(goal)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_goal(goal_id: uuid.UUID, current: CurrentUser, svc: GoalService = Depends(_svc)) -> Response:
    try:
        svc.soft_delete(current.id, goal_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)