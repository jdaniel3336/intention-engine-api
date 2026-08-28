import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, new_uuid


class CheckIn(Base):
    """Schema only for this pass — no endpoints/UI yet."""

    __tablename__ = "check_ins"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=new_uuid)
    intention_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("intentions.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    intention: Mapped["Intention"] = relationship(back_populates="check_ins")
