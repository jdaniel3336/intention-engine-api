import enum
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, new_uuid


class MilestoneStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=new_uuid)
    intention_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("intentions.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[MilestoneStatus] = mapped_column(
        SAEnum(MilestoneStatus, native_enum=False, length=32),
        default=MilestoneStatus.PENDING,
        nullable=False,
    )
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    intention: Mapped["Intention"] = relationship(back_populates="milestones")
    actions: Mapped[list["Action"]] = relationship(
        back_populates="milestone", cascade="all, delete-orphan", order_by="Action.priority"
    )
