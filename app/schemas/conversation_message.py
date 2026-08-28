import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.conversation_message import MessageRole


class MessageCreate(BaseModel):
    content: str


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    intention_id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime


class MessageTurnResponse(BaseModel):
    assistant_message: str
    ready_to_summarize: bool
    summary: str | None = None
