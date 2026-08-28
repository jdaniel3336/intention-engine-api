import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.milestone import MilestoneStatus
from app.schemas.action import ActionRead


class MilestoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    intention_id: uuid.UUID
    title: str
    description: str | None
    status: MilestoneStatus
    order: int
    target_date: date | None
    actions: list[ActionRead] = []
