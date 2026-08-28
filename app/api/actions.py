import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.action import Action, ActionStatus
from app.models.intention import Intention
from app.models.user import User
from app.schemas.action import ActionRead

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/{action_id}/complete", response_model=ActionRead)
def complete_action(
    action_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Action:
    action = (
        db.query(Action)
        .join(Intention, Action.intention_id == Intention.id)
        .filter(Action.id == action_id, Intention.user_id == current_user.id)
        .first()
    )
    if action is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")

    action.status = ActionStatus.COMPLETED
    action.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(action)
    return action
