"""
Digest service for orchestrating news digest generation.

This service handles the creation and management of personalized news digests.
It coordinates between NewsAPI (headlines), OpenAI (content generation), and
the database (persistence).

Key Concepts:
-------------
- digest_date: The date of the NEWS CONTENT, not when it was generated.
  A digest generated on Dec 3rd for "yesterday's news" has digest_date = Dec 2nd.

- Idempotency: generate_digest() is idempotent per (user_id, digest_date).
  Calling it multiple times with force=False returns the existing digest.

- Generation Sources:
  1. Scheduled: APScheduler calls at user's preferred_time daily
  2. Manual: User clicks "Generate Now" via POST /digests/generate
  Both use the same logic; scheduled calls pass explicit digest_date.

Usage Patterns:
---------------
- Scheduled generation: generate_digest(user_id, digest_date=yesterday, force=False)
- Manual generation: generate_digest(user_id, digest_date=None, force=False)
- Regeneration: generate_digest(user_id, digest_date=specific, force=True)
"""

import time as time_module
from datetime import date, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import NotFoundError
from src.logging_config import get_logger
from src.models.digest import Digest, DigestStatus
from src.models.user import User
from src.services.interest_service import InterestService
from src.services.news_service import get_news_service
from src.services.openai_service import get_openai_service

logger = get_logger("digest_service")


class DigestService:
    """Service for managing and generating news digests."""

    def __init__(self, db: AsyncSession):
        """
        Initialize digest service.

        Args:
            db: Database session.
        """
        self.db = db

    async def get_digest_by_id(
        self,
        digest_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> Optional[Digest]:
        """
        Get a digest by its ID.

        Args:
            digest_id: Digest unique identifier.
            user_id: Optional user ID to verify ownership.

        Returns:
            Optional[Digest]: Digest if found, None otherwise.
        """
        stmt = select(Digest).where(Digest.id == digest_id)
        if user_id:
            stmt = stmt.where(Digest.user_id == user_id)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_digest_by_date(
        self,
        user_id: UUID,
        digest_date: date,
    ) -> Optional[Digest]:
        """
        Get a user's digest for a specific date.

        Args:
            user_id: User's unique identifier.
            digest_date: Date of the digest.

        Returns:
            Optional[Digest]: Digest if found, None otherwise.
        """
        stmt = select(Digest).where(
            Digest.user_id == user_id,
            Digest.digest_date == digest_date,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_digests(
        self,
        user_id: UUID,
        page: int = 1,
        per_page: int = 10,
    ) -> Dict[str, Any]:
        """
        Get paginated list of user's digests.

        Args:
            user_id: User's unique identifier.
            page: Page number (1-indexed).
            per_page: Items per page.

        Returns:
            Dict with 'digests', 'total', 'page', 'per_page', 'has_next'.
        """
        # Get total count
        count_stmt = (
            select(func.count())
            .select_from(Digest)
            .where(Digest.user_id == user_id)
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get paginated results
        offset = (page - 1) * per_page
        stmt = (
            select(Digest)
            .where(Digest.user_id == user_id)
            .order_by(Digest.digest_date.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await self.db.execute(stmt)
        digests = list(result.scalars().all())

        has_next = (page * per_page) < total

        return {
            "digests": digests,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_next": has_next,
        }

    async def get_latest_digest(self, user_id: UUID) -> Optional[Digest]:
        """
        Get the user's most recent digest.

        Args:
            user_id: User's unique identifier.

        Returns:
            Optional[Digest]: Latest digest if exists.
        """
        stmt = (
            select(Digest)
            .where(Digest.user_id == user_id)
            .order_by(Digest.digest_date.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def generate_digest(
        self,
        user_id: UUID,
        digest_date: Optional[date] = None,
        force: bool = False,
    ) -> Digest:
        """
        Generate a news digest for a user.

        This is the main entry point for digest creation, used by both:
        - Scheduled generation (APScheduler at user's preferred_time)
        - Manual generation (POST /digests/generate)

        Idempotency:
        ------------
        Without force=True, this method is idempotent per (user_id, digest_date).
        If a completed digest exists, it's returned without regeneration.
        This ensures "Generate Now" and scheduled delivery don't conflict.

        Args:
            user_id: User's unique identifier.
            digest_date: Date of news content to include.
                        Defaults to yesterday (UTC) because:
                        1. NewsAPI free tier returns previous day's headlines
                        2. A "morning digest" summarizes yesterday's news
            force: If True, delete existing digest and regenerate.
                   Used only by explicit "regenerate" requests.

        Returns:
            Digest: The generated (or existing) digest.

        Raises:
            NotFoundError: If user not found.
            Various: On NewsAPI or OpenAI failures.
        """
        # Default to yesterday's date (UTC)
        # This is the date of the NEWS CONTENT, not the delivery date
        if digest_date is None:
            digest_date = date.today() - timedelta(days=1)

        logger.debug(
            f"generate_digest called: user_id={user_id}, "
            f"digest_date={digest_date}, force={force}"
        )

        # Check for existing digest (idempotency check)
        existing = await self.get_digest_by_date(user_id, digest_date)
        if existing:
            if not force and existing.status == DigestStatus.COMPLETED.value:
                logger.debug(
                    f"Returning existing digest for user {user_id} "
                    f"on {digest_date} (id={existing.id})"
                )
                return existing
            # If force=True, delete the existing digest to regenerate
            elif force:
                logger.info(
                    f"Force regenerating digest for user {user_id} "
                    f"on {digest_date}"
                )
                await self.delete_digest(existing.id, user_id)

        # Get user and their interests
        user_stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(user_stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User", str(user_id))

        # Get user's interests
        interest_service = InterestService(self.db)
        interests = await interest_service.get_user_interests(user_id)

        if not interests:
            logger.warning(f"User {user_id} has no interests selected")
            # Create a digest with a message about no interests
            digest = await self._create_empty_digest(
                user_id,
                digest_date,
                "No interests selected. Please add interests to receive personalized digests.",
            )
            return digest

        # Track generation time
        start_time = time_module.time()

        # Create pending digest
        digest = Digest(
            user_id=user_id,
            digest_date=digest_date,
            content="",
            status=DigestStatus.PENDING.value,
            interests_included=[i.slug for i in interests],
        )
        self.db.add(digest)
        await self.db.flush()

        try:
            # Prepare interest data for news service
            interest_data = [
                {"slug": i.slug, "newsapi_category": i.newsapi_category}
                for i in interests
            ]

            # Fetch headlines
            news_service = await get_news_service()
            headlines = await news_service.get_previous_day_headlines(interest_data)

            # Generate digest content
            openai_service = await get_openai_service()
            # Format date as human-readable string for Claude (e.g., "November 30, 2025")
            formatted_date = digest_date.strftime("%B %d, %Y")
            result = await openai_service.generate_digest(
                headlines=headlines,
                digest_date=formatted_date,
                interests=[i.slug for i in interests],
            )

            # Calculate generation time
            generation_time_ms = int((time_module.time() - start_time) * 1000)

            # Update digest with content
            digest.content = result["content"]
            digest.summary = result["summary"]
            digest.word_count = result["word_count"]
            digest.headlines_used = headlines
            digest.status = DigestStatus.COMPLETED.value
            digest.generation_time_ms = generation_time_ms

            await self.db.flush()
            await self.db.refresh(digest)

            logger.info(
                f"Generated digest for user {user_id}: "
                f"{result['word_count']} words, "
                f"{len(headlines)} headlines, "
                f"{generation_time_ms}ms"
            )

            return digest

        except Exception as e:
            logger.error(f"Digest generation failed for user {user_id}: {e}")
            digest.status = DigestStatus.FAILED.value
            digest.error_message = str(e)
            digest.content = "Digest generation failed. Please try again later."
            await self.db.flush()
            raise

    async def _create_empty_digest(
        self,
        user_id: UUID,
        digest_date: date,
        message: str,
    ) -> Digest:
        """
        Create an empty/placeholder digest.

        Args:
            user_id: User's unique identifier.
            digest_date: Date for the digest.
            message: Message to include in the digest.

        Returns:
            Digest: Created digest.
        """
        # Format the date nicely for the header
        formatted_date = digest_date.strftime("%B %d, %Y")
        content = f"# Daily News Digest – {formatted_date}\n\n**Executive Summary:** {message}\n\n## Key Takeaways\n- {message}"

        digest = Digest(
            user_id=user_id,
            digest_date=digest_date,
            content=content,
            summary=message[:200],
            status=DigestStatus.COMPLETED.value,
            word_count=len(content.split()),
            interests_included=[],
            headlines_used=[],
        )

        self.db.add(digest)
        await self.db.flush()
        await self.db.refresh(digest)

        return digest

    async def delete_digest(
        self,
        digest_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Delete a digest.

        Args:
            digest_id: Digest unique identifier.
            user_id: User ID for ownership verification.

        Returns:
            bool: True if deleted, False if not found.
        """
        digest = await self.get_digest_by_id(digest_id, user_id)
        if not digest:
            return False

        await self.db.delete(digest)
        await self.db.flush()

        logger.info(f"Deleted digest {digest_id} for user {user_id}")
        return True
