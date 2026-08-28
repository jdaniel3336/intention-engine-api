import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.intention import IntentionStatus
from app.schemas.milestone import MilestoneRead


class IntentionCreate(BaseModel):
    title: str
    description: str | None = None


class IntentionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    desired_outcome: str | None = None
    status: IntentionStatus | None = None
    target_date: date | None = None
    budget: Decimal | None = None


class IntentionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str | None
    desired_outcome: str | None
    status: IntentionStatus
    target_date: date | None
    budget: Decimal | None
    created_at: datetime
    updated_at: datetime
    milestones: list[MilestoneRead] = []
