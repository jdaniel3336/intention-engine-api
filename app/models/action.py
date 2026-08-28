import enum
import uuid
from datetime import date, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Date as SADate
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, new_uuid


class ActionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=new_uuid)
    milestone_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("milestones.id"), nullable=False, index=True
    )
    intention_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("intentions.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ActionStatus] = mapped_column(
        SAEnum(ActionStatus, native_enum=False, length=32),
        default=ActionStatus.PENDING,
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    due_date: Mapped[date | None] = mapped_column(SADate, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    milestone: Mapped["Milestone"] = relationship(back_populates="actions")
    intention: Mapped["Intention"] = relationship(back_populates="actions")
