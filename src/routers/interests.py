"""
Interest management routes.
"""

from typing import List

from fastapi import APIRouter, status

from src.dependencies import CurrentUser, DbSession
from src.logging_config import get_logger
from src.schemas.interest import InterestListResponse, InterestResponse, UserInterestUpdate
from src.services.interest_service import InterestService

logger = get_logger("interests_router")

router = APIRouter(prefix="/interests", tags=["Interests"])


@router.get(
    "",
    response_model=InterestListResponse,
    summary="List all available interests",
    description="""
    Get a list of all available news interest categories.
    
    Users can subscribe to these interests to customize their daily digest.
    """,
    responses={
        200: {"description": "List of interests retrieved successfully"},
    },
)
async def list_interests(
    db: DbSession,
) -> InterestListResponse:
    """Get all available interests."""
    interest_service = InterestService(db)
    interests = await interest_service.get_all_interests()

    return InterestListResponse(
        interests=[InterestResponse.model_validate(i) for i in interests],
        total=len(interests),
    )


@router.get(
    "/me",
    response_model=List[InterestResponse],
    summary="Get current user's interests",
    description="""
    Get the list of interests the authenticated user is subscribed to.
    """,
    responses={
        200: {"description": "User's interests retrieved successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def get_my_interests(
    current_user: CurrentUser,
    db: DbSession,
) -> List[InterestResponse]:
    """Get the current user's subscribed interests."""
    interest_service = InterestService(db)
    interests = await interest_service.get_user_interests(current_user.id)

    return [InterestResponse.model_validate(i) for i in interests]


@router.put(
    "/me",
    response_model=List[InterestResponse],
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
async def update_my_interests(
    interest_update: UserInterestUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> List[InterestResponse]:
    """Update the current user's subscribed interests."""
    interest_service = InterestService(db)
    interests = await interest_service.update_user_interests(
        user_id=current_user.id,
        interest_slugs=interest_update.interest_slugs,
    )

    logger.info(
        f"User {current_user.email} updated interests: "
        f"{[i.slug for i in interests]}"
    )

    return [InterestResponse.model_validate(i) for i in interests]


@router.post(
    "/me/{interest_slug}",
    response_model=InterestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a single interest",
    description="""
    Add a single interest to the user's subscriptions.
    
    If the user is already subscribed, returns the existing interest.
    """,
    responses={
        201: {"description": "Interest added successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Interest not found"},
    },
)
async def add_interest(
    interest_slug: str,
    current_user: CurrentUser,
    db: DbSession,
) -> InterestResponse:
    """Add a single interest to the user's subscriptions."""
    interest_service = InterestService(db)
    interest = await interest_service.add_interest_to_user(
        user_id=current_user.id,
        interest_slug=interest_slug,
    )

    logger.info(f"User {current_user.email} added interest: {interest_slug}")

    return InterestResponse.model_validate(interest)


@router.delete(
    "/me/{interest_slug}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a single interest",
    description="""
    Remove a single interest from the user's subscriptions.
    """,
    responses={
        204: {"description": "Interest removed successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Interest not found"},
    },
)
async def remove_interest(
    interest_slug: str,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Remove a single interest from the user's subscriptions."""
    interest_service = InterestService(db)
    await interest_service.remove_interest_from_user(
        user_id=current_user.id,
        interest_slug=interest_slug,
    )

    logger.info(f"User {current_user.email} removed interest: {interest_slug}")
