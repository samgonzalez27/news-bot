"""
Interest schemas for request/response validation.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InterestCreate(BaseModel):
    """Request schema for creating an interest (admin only)."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Display name for the interest",
        examples=["Technology"],
    )
    slug: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern=r"^[a-z0-9-]+$",
        description="URL-friendly identifier",
        examples=["technology"],
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Brief description of the interest",
    )
    newsapi_category: Optional[str] = Field(
        None,
        max_length=50,
        description="Corresponding NewsAPI category",
    )
    display_order: int = Field(
        default=0,
        ge=0,
        description="Display order in listings",
    )


class InterestResponse(BaseModel):
    """Response schema for interest data."""

    id: UUID = Field(..., description="Unique interest identifier")
    name: str = Field(..., description="Display name")
    slug: str = Field(..., description="URL-friendly identifier")
    description: Optional[str] = Field(None, description="Brief description")
    is_active: bool = Field(..., description="Whether the interest is active")
    display_order: int = Field(..., description="Display order")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Technology",
                "slug": "technology",
                "description": "Tech industry and innovation news",
                "is_active": True,
                "display_order": 5,
                "created_at": "2024-01-15T10:30:00Z",
            }
        },
    }


class InterestListResponse(BaseModel):
    """Response schema for list of interests."""

    interests: List[InterestResponse] = Field(
        ...,
        description="List of available interests",
    )
    total: int = Field(..., description="Total number of interests")


class UserInterestUpdate(BaseModel):
    """Request schema for updating user's interests."""

    interest_slugs: List[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of interest slugs to subscribe to",
        examples=[["technology", "science", "economics"]],
    )
