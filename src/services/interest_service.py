"""
Interest service for managing user interests.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import NotFoundError
from src.logging_config import get_logger
from src.models.interest import Interest, PREDEFINED_INTERESTS
from src.models.user import User, UserInterest

logger = get_logger("interest_service")


class InterestService:
    """Service for interest management."""

    def __init__(self, db: AsyncSession):
        """
        Initialize interest service.

        Args:
            db: Database session.
        """
        self.db = db

    async def get_all_interests(self, active_only: bool = True) -> List[Interest]:
        """
        Get all available interests.

        Args:
            active_only: If True, only return active interests.

        Returns:
            List[Interest]: List of interests ordered by display_order.
        """
        stmt = select(Interest).order_by(Interest.display_order)
        if active_only:
            stmt = stmt.where(Interest.is_active.is_(True))

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Optional[Interest]:
        """
        Get an interest by its slug.

        Args:
            slug: Interest slug identifier.

        Returns:
            Optional[Interest]: Interest if found, None otherwise.
        """
        stmt = select(Interest).where(Interest.slug == slug)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slugs(self, slugs: List[str]) -> List[Interest]:
        """
        Get multiple interests by their slugs.

        Args:
            slugs: List of interest slugs.

        Returns:
            List[Interest]: List of found interests.
        """
        stmt = select(Interest).where(Interest.slug.in_(slugs))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_interests(self, user_id: UUID) -> List[Interest]:
        """
        Get all interests for a specific user.

        Args:
            user_id: User's unique identifier.

        Returns:
            List[Interest]: User's subscribed interests.
        """
        stmt = (
            select(Interest)
            .join(UserInterest)
            .where(UserInterest.user_id == user_id)
            .order_by(Interest.display_order)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_user_interests(
        self,
        user_id: UUID,
        interest_slugs: List[str],
    ) -> List[Interest]:
        """
        Update a user's subscribed interests.

        Replaces all existing interests with the new list.

        Args:
            user_id: User's unique identifier.
            interest_slugs: List of interest slugs to subscribe to.

        Returns:
            List[Interest]: Updated list of user's interests.

        Raises:
            NotFoundError: If user or any interest not found.
        """
        # Verify user exists
        user_stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(user_stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User", str(user_id))

        # Get interests by slugs
        interests = await self.get_by_slugs(interest_slugs)
        found_slugs = {i.slug for i in interests}
        missing_slugs = set(interest_slugs) - found_slugs

        if missing_slugs:
            raise NotFoundError(
                "Interest",
                f"slugs: {', '.join(missing_slugs)}",
            )

        # Remove existing user interests
        delete_stmt = (
            UserInterest.__table__.delete()
            .where(UserInterest.user_id == user_id)
        )
        await self.db.execute(delete_stmt)

        # Add new interests
        for interest in interests:
            user_interest = UserInterest(
                user_id=user_id,
                interest_id=interest.id,
            )
            self.db.add(user_interest)

        await self.db.flush()

        logger.info(
            f"Updated interests for user {user_id}: "
            f"{[i.slug for i in interests]}"
        )
        return interests

    async def add_interest_to_user(
        self,
        user_id: UUID,
        interest_slug: str,
    ) -> Interest:
        """
        Add a single interest to a user.

        Args:
            user_id: User's unique identifier.
            interest_slug: Interest slug to add.

        Returns:
            Interest: Added interest.

        Raises:
            NotFoundError: If interest not found.
        """
        interest = await self.get_by_slug(interest_slug)
        if not interest:
            raise NotFoundError("Interest", interest_slug)

        # Check if already subscribed
        existing_stmt = select(UserInterest).where(
            UserInterest.user_id == user_id,
            UserInterest.interest_id == interest.id,
        )
        result = await self.db.execute(existing_stmt)
        if result.scalar_one_or_none():
            logger.debug(f"User {user_id} already has interest {interest_slug}")
            return interest

        # Add the interest
        user_interest = UserInterest(
            user_id=user_id,
            interest_id=interest.id,
        )
        self.db.add(user_interest)
        await self.db.flush()

        logger.info(f"Added interest {interest_slug} to user {user_id}")
        return interest

    async def remove_interest_from_user(
        self,
        user_id: UUID,
        interest_slug: str,
    ) -> None:
        """
        Remove a single interest from a user.

        Args:
            user_id: User's unique identifier.
            interest_slug: Interest slug to remove.

        Raises:
            NotFoundError: If interest not found.
        """
        interest = await self.get_by_slug(interest_slug)
        if not interest:
            raise NotFoundError("Interest", interest_slug)

        delete_stmt = (
            UserInterest.__table__.delete()
            .where(UserInterest.user_id == user_id)
            .where(UserInterest.interest_id == interest.id)
        )
        await self.db.execute(delete_stmt)
        await self.db.flush()

        logger.info(f"Removed interest {interest_slug} from user {user_id}")

    async def seed_interests(self) -> int:
        """
        Seed predefined interests into the database.

        Only adds interests that don't already exist.

        Returns:
            int: Number of interests created.
        """
        created_count = 0

        for interest_data in PREDEFINED_INTERESTS:
            existing = await self.get_by_slug(interest_data["slug"])
            if existing:
                continue

            interest = Interest(**interest_data)
            self.db.add(interest)
            created_count += 1

        if created_count > 0:
            await self.db.flush()
            logger.info(f"Seeded {created_count} interests")

        return created_count
