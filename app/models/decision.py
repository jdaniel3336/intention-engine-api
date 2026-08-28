import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, new_uuid


class Decision(Base):
    """Schema only for this pass — no endpoints/UI yet."""

    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=new_uuid)
    intention_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("intentions.id"), nullable=False, index=True
    )
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    intention: Mapped["Intention"] = relationship(back_populates="decisions")
