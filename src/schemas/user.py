"""
User schemas for request/response validation.
"""

import re
from datetime import datetime, time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Request schema for user registration."""

    email: EmailStr = Field(
        ...,
        description="User's email address (used for login)",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 characters, must contain letter and number)",
        examples=["SecurePass123"],
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's full name",
        examples=["John Doe"],
    )
    preferred_time: str = Field(
        default="08:00",
        description="Preferred digest delivery time in HH:MM format (UTC)",
        examples=["08:00", "18:30"],
    )
    # NOTE: Timezone support disabled - all users use UTC
    # Uncomment to re-enable custom timezone support
    # timezone: str = Field(
    #     default="UTC",
    #     description="User's timezone (IANA format)",
    #     examples=["UTC", "America/New_York", "Europe/London"],
    # )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password contains at least one letter and one number."""
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v

    @field_validator("preferred_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time is in HH:MM format."""
        try:
            time.fromisoformat(v)
        except ValueError:
            raise ValueError("Time must be in HH:MM format")
        return v

    # NOTE: Timezone support disabled - all users use UTC
    # Uncomment to re-enable custom timezone support
    # @field_validator("timezone")
    # @classmethod
    # def validate_timezone(cls, v: str) -> str:
    #     """Validate timezone is a valid IANA timezone."""
    #     try:
    #         import zoneinfo
    #
    #         zoneinfo.ZoneInfo(v)
    #     except Exception:
    #         raise ValueError(f"Invalid timezone: {v}")
    #     return v


class UserUpdate(BaseModel):
    """Request schema for updating user profile."""

    full_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="User's full name",
    )
    email: Optional[EmailStr] = Field(
        None,
        description="User's email address",
    )

    model_config = {"extra": "forbid"}


class UserPreferencesUpdate(BaseModel):
    """Request schema for updating user preferences."""

    preferred_time: Optional[str] = Field(
        None,
        description="Preferred digest delivery time in HH:MM format (UTC)",
        examples=["08:00", "18:30"],
    )
    # NOTE: Timezone support disabled - all users use UTC
    # Uncomment to re-enable custom timezone support
    # timezone: Optional[str] = Field(
    #     None,
    #     description="User's timezone (IANA format)",
    #     examples=["UTC", "America/New_York"],
    # )

    @field_validator("preferred_time")
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate time is in HH:MM format."""
        if v is not None:
            try:
                time.fromisoformat(v)
            except ValueError:
                raise ValueError("Time must be in HH:MM format")
        return v

    # NOTE: Timezone support disabled - all users use UTC
    # Uncomment to re-enable custom timezone support
    # @field_validator("timezone")
    # @classmethod
    # def validate_timezone(cls, v: Optional[str]) -> Optional[str]:
    #     """Validate timezone is a valid IANA timezone."""
    #     if v is not None:
    #         try:
    #             import zoneinfo
    #
    #             zoneinfo.ZoneInfo(v)
    #         except Exception:
    #             raise ValueError(f"Invalid timezone: {v}")
    #     return v

    model_config = {"extra": "forbid"}


class InterestSummary(BaseModel):
    """Summary schema for interest in user response."""

    id: UUID
    slug: str
    name: str

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    """Response schema for user data."""

    id: UUID = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User's email address")
    full_name: str = Field(..., description="User's full name")
    preferred_time: str = Field(..., description="Preferred digest delivery time (UTC)")
    # NOTE: Timezone support disabled - all users use UTC
    # Uncomment to re-enable custom timezone support
    # timezone: str = Field(..., description="User's timezone")
    is_active: bool = Field(..., description="Whether the account is active")
    interests: List[InterestSummary] = Field(
        default_factory=list,
        description="User's selected interests",
    )
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "preferred_time": "08:00",
                # "timezone": "America/New_York",  # Timezone support disabled
                "is_active": True,
                "interests": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "slug": "technology",
                        "name": "Technology",
                    }
                ],
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        },
    }

    @field_validator("preferred_time", mode="before")
    @classmethod
    def format_time(cls, v):
        """Format time object to string."""
        if isinstance(v, time):
            return v.strftime("%H:%M")
        return v
