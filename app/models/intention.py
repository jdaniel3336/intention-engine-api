import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, new_uuid


class IntentionStatus(str, enum.Enum):
    CLARIFYING = "clarifying"
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


class Intention(Base):
    __tablename__ = "intentions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    desired_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[IntentionStatus] = mapped_column(
        SAEnum(IntentionStatus, native_enum=False, length=32),
        default=IntentionStatus.CLARIFYING,
        nullable=False,
    )
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="intentions")
    milestones: Mapped[list["Milestone"]] = relationship(
        back_populates="intention", cascade="all, delete-orphan", order_by="Milestone.order"
    )
    actions: Mapped[list["Action"]] = relationship(back_populates="intention", cascade="all, delete-orphan")
    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="intention", cascade="all, delete-orphan", order_by="ConversationMessage.created_at"
    )
    expenses: Mapped[list["Expense"]] = relationship(back_populates="intention", cascade="all, delete-orphan")
    decisions: Mapped[list["Decision"]] = relationship(back_populates="intention", cascade="all, delete-orphan")
    check_ins: Mapped[list["CheckIn"]] = relationship(back_populates="intention", cascade="all, delete-orphan")
