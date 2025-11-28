# Schemas Package
from src.schemas.auth import LoginRequest, TokenResponse
from src.schemas.digest import (
    DigestCreate,
    DigestResponse,
    DigestListResponse,
    DigestSummary,
)
from src.schemas.interest import InterestCreate, InterestResponse, InterestListResponse
from src.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserPreferencesUpdate,
)

__all__ = [
    # Auth
    "LoginRequest",
    "TokenResponse",
    # User
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "UserPreferencesUpdate",
    # Interest
    "InterestCreate",
    "InterestResponse",
    "InterestListResponse",
    # Digest
    "DigestCreate",
    "DigestResponse",
    "DigestListResponse",
    "DigestSummary",
]
