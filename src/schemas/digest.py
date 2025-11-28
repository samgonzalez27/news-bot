"""
Digest schemas for request/response validation.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class HeadlineInfo(BaseModel):
    """Schema for headline information stored in digest."""

    title: str = Field(..., description="Article headline")
    source: str = Field(..., description="Source name")
    url: str = Field(..., description="Article URL")
    published_at: str = Field(..., description="Publication timestamp")
    category: str = Field(..., description="News category")


class DigestCreate(BaseModel):
    """Request schema for manual digest generation."""

    digest_date: Optional[date] = Field(
        None,
        description="Date for the digest (defaults to yesterday)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "digest_date": "2024-01-14",
            }
        }
    }


class DigestResponse(BaseModel):
    """Response schema for digest data."""

    id: UUID = Field(..., description="Unique digest identifier")
    user_id: UUID = Field(..., description="Owner user ID")
    digest_date: date = Field(..., description="Date the news is from")
    content: str = Field(..., description="Full digest content (Markdown)")
    summary: Optional[str] = Field(None, description="Brief summary")
    headlines_used: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Headlines used to generate the digest",
    )
    interests_included: List[str] = Field(
        default_factory=list,
        description="Interest categories included",
    )
    word_count: Optional[int] = Field(None, description="Word count of content")
    status: str = Field(..., description="Generation status")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "digest_date": "2024-01-14",
                "content": "# Daily News Digest\n\n## Technology\n\n...",
                "summary": "Key developments in tech, economics, and science",
                "headlines_used": [
                    {
                        "title": "Major Tech Announcement",
                        "source": "TechNews",
                        "url": "https://example.com/article",
                        "published_at": "2024-01-14T10:00:00Z",
                        "category": "technology",
                    }
                ],
                "interests_included": ["technology", "economics"],
                "word_count": 850,
                "status": "completed",
                "created_at": "2024-01-15T08:00:00Z",
            }
        },
    }


class DigestSummary(BaseModel):
    """Summary schema for digest listings."""

    id: UUID = Field(..., description="Unique digest identifier")
    digest_date: date = Field(..., description="Date the news is from")
    summary: Optional[str] = Field(None, description="Brief summary")
    interests_included: List[str] = Field(
        default_factory=list,
        description="Interest categories included",
    )
    word_count: Optional[int] = Field(None, description="Word count")
    status: str = Field(..., description="Generation status")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {"from_attributes": True}


class DigestListResponse(BaseModel):
    """Response schema for paginated digest list."""

    digests: List[DigestSummary] = Field(
        ...,
        description="List of digest summaries",
    )
    total: int = Field(..., description="Total number of digests")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether more pages exist")
