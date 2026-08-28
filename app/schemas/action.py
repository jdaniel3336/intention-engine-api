import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.action import ActionStatus


class ActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    milestone_id: uuid.UUID
    intention_id: uuid.UUID
    title: str
    description: str | None
    status: ActionStatus
    priority: int
    due_date: date | None
    created_at: datetime
    completed_at: datetime | None
