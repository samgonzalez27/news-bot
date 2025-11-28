"""
Digest model for generated news digests.
"""

import uuid
from datetime import date, datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List

from sqlalchemy import Date, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from src.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class DigestStatus(str, Enum):
    """Status of digest generation."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Digest(Base):
    """Generated news digest model."""

    __tablename__ = "digests"
    __table_args__ = (
        UniqueConstraint("user_id", "digest_date", name="uq_user_digest_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    digest_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    summary: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    headlines_used: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    interests_included: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    word_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    generation_time_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DigestStatus.COMPLETED.value,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="digests",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Digest(id={self.id}, user_id={self.user_id}, date={self.digest_date})>"
