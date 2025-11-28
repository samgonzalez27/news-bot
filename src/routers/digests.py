"""
Digest management routes.
"""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, status

from src.dependencies import CurrentUser, DbSession
from src.exceptions import NotFoundError
from src.logging_config import get_logger
from src.schemas.digest import DigestCreate, DigestListResponse, DigestResponse, DigestSummary
from src.services.digest_service import DigestService

logger = get_logger("digests_router")

router = APIRouter(prefix="/digests", tags=["Digests"])


@router.get(
    "",
    response_model=DigestListResponse,
    summary="List user's digests",
    description="""
    Get a paginated list of the user's news digests.
    
    Digests are ordered by date, most recent first.
    """,
    responses={
        200: {"description": "Digest list retrieved successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def list_digests(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=50, description="Items per page"),
) -> DigestListResponse:
    """Get paginated list of user's digests."""
    digest_service = DigestService(db)
    result = await digest_service.get_user_digests(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
    )

    return DigestListResponse(
        digests=[DigestSummary.model_validate(d) for d in result["digests"]],
        total=result["total"],
        page=result["page"],
        per_page=result["per_page"],
        has_next=result["has_next"],
    )


@router.get(
    "/latest",
    response_model=DigestResponse,
    summary="Get latest digest",
    description="""
    Get the user's most recent news digest.
    """,
    responses={
        200: {"description": "Latest digest retrieved successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "No digests found"},
    },
)
async def get_latest_digest(
    current_user: CurrentUser,
    db: DbSession,
) -> DigestResponse:
    """Get the user's most recent digest."""
    digest_service = DigestService(db)
    digest = await digest_service.get_latest_digest(current_user.id)

    if not digest:
        raise NotFoundError("Digest")

    return DigestResponse.model_validate(digest)


@router.get(
    "/by-date/{digest_date}",
    response_model=DigestResponse,
    summary="Get digest by date",
    description="""
    Get the user's digest for a specific date.
    
    The date should be in YYYY-MM-DD format.
    """,
    responses={
        200: {"description": "Digest retrieved successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Digest not found for this date"},
    },
)
async def get_digest_by_date(
    digest_date: date,
    current_user: CurrentUser,
    db: DbSession,
) -> DigestResponse:
    """Get digest for a specific date."""
    digest_service = DigestService(db)
    digest = await digest_service.get_digest_by_date(
        user_id=current_user.id,
        digest_date=digest_date,
    )

    if not digest:
        raise NotFoundError("Digest", digest_date.isoformat())

    return DigestResponse.model_validate(digest)


@router.get(
    "/{digest_id}",
    response_model=DigestResponse,
    summary="Get digest by ID",
    description="""
    Get a specific digest by its unique identifier.
    """,
    responses={
        200: {"description": "Digest retrieved successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Digest not found"},
    },
)
async def get_digest(
    digest_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> DigestResponse:
    """Get a specific digest by ID."""
    digest_service = DigestService(db)
    digest = await digest_service.get_digest_by_id(
        digest_id=digest_id,
        user_id=current_user.id,
    )

    if not digest:
        raise NotFoundError("Digest", str(digest_id))

    return DigestResponse.model_validate(digest)


@router.post(
    "/generate",
    response_model=DigestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new digest",
    description="""
    Manually trigger digest generation.
    
    By default, generates a digest for yesterday's news.
    Optionally specify a date to generate for a different day.
    
    Note: This endpoint is rate-limited to 1 request per hour.
    """,
    responses={
        201: {"description": "Digest generated successfully"},
        400: {"description": "Validation error"},
        401: {"description": "Not authenticated"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "External API error"},
    },
)
async def generate_digest(
    current_user: CurrentUser,
    db: DbSession,
    request: Optional[DigestCreate] = None,
) -> DigestResponse:
    """Manually trigger digest generation."""
    digest_date = request.digest_date if request else None

    digest_service = DigestService(db)
    digest = await digest_service.generate_digest(
        user_id=current_user.id,
        digest_date=digest_date,
        force=False,  # Don't regenerate if already exists
    )

    logger.info(
        f"Generated digest for user {current_user.email}: "
        f"{digest.digest_date}"
    )

    return DigestResponse.model_validate(digest)


@router.post(
    "/regenerate/{digest_date}",
    response_model=DigestResponse,
    summary="Regenerate a digest",
    description="""
    Force regeneration of a digest for a specific date.
    
    This will replace any existing digest for that date.
    """,
    responses={
        200: {"description": "Digest regenerated successfully"},
        401: {"description": "Not authenticated"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "External API error"},
    },
)
async def regenerate_digest(
    digest_date: date,
    current_user: CurrentUser,
    db: DbSession,
) -> DigestResponse:
    """Force regenerate a digest for a specific date."""
    digest_service = DigestService(db)
    digest = await digest_service.generate_digest(
        user_id=current_user.id,
        digest_date=digest_date,
        force=True,
    )

    logger.info(
        f"Regenerated digest for user {current_user.email}: "
        f"{digest.digest_date}"
    )

    return DigestResponse.model_validate(digest)


@router.delete(
    "/{digest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a digest",
    description="""
    Delete a specific digest by its ID.
    """,
    responses={
        204: {"description": "Digest deleted successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Digest not found"},
    },
)
async def delete_digest(
    digest_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a specific digest."""
    digest_service = DigestService(db)
    deleted = await digest_service.delete_digest(
        digest_id=digest_id,
        user_id=current_user.id,
    )

    if not deleted:
        raise NotFoundError("Digest", str(digest_id))

    logger.info(f"Deleted digest {digest_id} for user {current_user.email}")
