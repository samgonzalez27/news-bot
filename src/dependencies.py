"""
FastAPI dependencies for the News Digest API.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.exceptions import AuthenticationError, NotFoundError
from src.models.user import User
from src.services.auth_service import AuthService
from src.services.user_service import UserService


async def get_token_from_header(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """
    Extract JWT token from Authorization header.

    Args:
        authorization: Authorization header value.

    Returns:
        str: JWT token.

    Raises:
        AuthenticationError: If header is missing or invalid.
    """
    if not authorization:
        raise AuthenticationError("Missing authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid authorization header format")

    return parts[1]


async def get_current_user_id(
    token: Annotated[str, Depends(get_token_from_header)],
) -> UUID:
    """
    Get the current user's ID from the JWT token.

    Args:
        token: JWT token from header.

    Returns:
        UUID: User's unique identifier.

    Raises:
        AuthenticationError: If token is invalid.
    """
    return AuthService.get_user_id_from_token(token)


async def get_current_user(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get the current authenticated user.

    Args:
        user_id: User ID from token.
        db: Database session.

    Returns:
        User: Current user object.

    Raises:
        AuthenticationError: If user not found or inactive.
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise AuthenticationError("User not found")

    if not user.is_active:
        raise AuthenticationError("User account is deactivated")

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Alias for get_current_user that explicitly requires active status.

    This is semantically clearer in route definitions.

    Args:
        current_user: Current authenticated user.

    Returns:
        User: Active user object.
    """
    return current_user


# Type aliases for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserId = Annotated[UUID, Depends(get_current_user_id)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
