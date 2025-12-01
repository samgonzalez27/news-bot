"""
User management routes.
"""

from typing import List

from fastapi import APIRouter, status

from src.dependencies import CurrentUser, DbSession
from src.logging_config import get_logger
from src.schemas.interest import InterestResponse, UserInterestUpdate
from src.schemas.user import UserPreferencesUpdate, UserResponse, UserUpdate
from src.services.interest_service import InterestService
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


@router.put(
    "/me/interests",
    response_model=UserResponse,
    summary="Update user's interests",
    description="""
    Replace the user's subscribed interests with a new list.
    
    Provide a list of interest slugs (e.g., ["technology", "economics"]).
    This replaces all existing subscriptions.
    """,
    responses={
        200: {"description": "Interests updated successfully"},
        400: {"description": "Validation error"},
        401: {"description": "Not authenticated"},
        404: {"description": "One or more interests not found"},
    },
)
async def update_user_interests(
    interest_update: UserInterestUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> UserResponse:
    """Update the current user's subscribed interests."""
    interest_service = InterestService(db)
    updated_interests = await interest_service.update_user_interests(
        user_id=current_user.id,
        interest_slugs=interest_update.interest_slugs,
    )

    # Build response with updated interests directly from the service result
    # This avoids SQLAlchemy session caching issues
    from src.schemas.user import InterestSummary
    
    response_data = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "preferred_time": current_user.preferred_time,
        "timezone": current_user.timezone,
        "is_active": current_user.is_active,
        "interests": [InterestSummary.model_validate(i) for i in updated_interests],
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
    }

    logger.info(
        f"User {current_user.email} updated interests via /users/me/interests"
    )

    return UserResponse(**response_data)


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
