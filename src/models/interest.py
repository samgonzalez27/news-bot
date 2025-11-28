"""
Interest model for news categories.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class Interest(Base):
    """Interest/category model for news topics."""

    __tablename__ = "interests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    newsapi_category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_interests",
        back_populates="interests",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Interest(id={self.id}, slug={self.slug})>"


# Predefined interests data for seeding
PREDEFINED_INTERESTS = [
    {
        "name": "Economics",
        "slug": "economics",
        "description": "Business, markets, and economic news",
        "newsapi_category": "business",
        "display_order": 1,
    },
    {
        "name": "Politics",
        "slug": "politics",
        "description": "Political news and policy updates",
        "newsapi_category": "general",
        "display_order": 2,
    },
    {
        "name": "Foreign Affairs",
        "slug": "foreign-affairs",
        "description": "International relations and global news",
        "newsapi_category": "general",
        "display_order": 3,
    },
    {
        "name": "Sports",
        "slug": "sports",
        "description": "Sports news and updates",
        "newsapi_category": "sports",
        "display_order": 4,
    },
    {
        "name": "Technology",
        "slug": "technology",
        "description": "Tech industry and innovation news",
        "newsapi_category": "technology",
        "display_order": 5,
    },
    {
        "name": "Science",
        "slug": "science",
        "description": "Scientific discoveries and research",
        "newsapi_category": "science",
        "display_order": 6,
    },
    {
        "name": "Health",
        "slug": "health",
        "description": "Health, medicine, and wellness news",
        "newsapi_category": "health",
        "display_order": 7,
    },
    {
        "name": "Entertainment",
        "slug": "entertainment",
        "description": "Entertainment and celebrity news",
        "newsapi_category": "entertainment",
        "display_order": 8,
    },
]
