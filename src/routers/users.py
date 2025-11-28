"""
User management routes.
"""

from fastapi import APIRouter, status

from src.dependencies import CurrentUser, DbSession
from src.logging_config import get_logger
from src.schemas.user import UserPreferencesUpdate, UserResponse, UserUpdate
from src.services.user_service import UserService

logger = get_logger("users_router")

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="""
    Retrieve the authenticated user's profile information,
    including their selected interests and preferences.
    """,
    responses={
        200: {"description": "User profile retrieved successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def get_current_user_profile(
    current_user: CurrentUser,
) -> UserResponse:
    """Get the current user's profile."""
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="""
    Update the authenticated user's profile information.
    
    Only provided fields will be updated. Omit fields you don't want to change.
    """,
    responses={
        200: {"description": "Profile updated successfully"},
        400: {"description": "Validation error"},
        401: {"description": "Not authenticated"},
        409: {"description": "Email already in use"},
    },
)
async def update_current_user_profile(
    update_data: UserUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> UserResponse:
    """Update the current user's profile."""
    user_service = UserService(db)
    updated_user = await user_service.update_user(
        user_id=current_user.id,
        update_data=update_data,
    )

    logger.info(f"User profile updated: {updated_user.email}")

    return UserResponse.model_validate(updated_user)


@router.patch(
    "/me/preferences",
    response_model=UserResponse,
    summary="Update digest preferences",
    description="""
    Update the user's digest delivery preferences.
    
    - **preferred_time**: Time to receive digest (HH:MM format, 24-hour)
    - **timezone**: IANA timezone identifier (e.g., "America/New_York")
    """,
    responses={
        200: {"description": "Preferences updated successfully"},
        400: {"description": "Validation error"},
        401: {"description": "Not authenticated"},
    },
)
async def update_preferences(
    preferences: UserPreferencesUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> UserResponse:
    """Update the current user's digest preferences."""
    user_service = UserService(db)
    updated_user = await user_service.update_preferences(
        user_id=current_user.id,
        preferences=preferences,
    )

    logger.info(f"User preferences updated: {updated_user.email}")

    return UserResponse.model_validate(updated_user)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate current user account",
    description="""
    Deactivate the authenticated user's account.
    
    This is a soft delete - the account can potentially be reactivated.
    The user will no longer be able to log in.
    """,
    responses={
        204: {"description": "Account deactivated successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def deactivate_account(
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Deactivate the current user's account."""
    user_service = UserService(db)
    await user_service.deactivate_user(current_user.id)

    logger.info(f"User account deactivated: {current_user.email}")
