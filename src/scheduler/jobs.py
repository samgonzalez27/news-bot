"""
Scheduled job definitions for digest generation.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import get_async_session_maker
from src.logging_config import get_logger
from src.models.user import User
from src.scheduler.scheduler import scheduler
from src.services.digest_service import DigestService
from src.services.interest_service import InterestService

logger = get_logger("scheduler_jobs")


async def get_users_due_for_digest(
    db: AsyncSession,
    current_time_utc: datetime,
    window_minutes: int = 15,
) -> List[User]:
    """
    Get users whose preferred digest time falls within the current window.

    Args:
        db: Database session.
        current_time_utc: Current UTC time.
        window_minutes: Size of the time window to check.

    Returns:
        List of users due for digest generation.
    """
    # We need to check users whose local preferred time
    # falls within the current window
    # This is a simplified approach - for production, consider
    # using proper timezone-aware queries

    window_start = current_time_utc.time()
    window_end = (current_time_utc + timedelta(minutes=window_minutes)).time()

    # Handle midnight crossing
    if window_end < window_start:
        # Query needs to handle wrap-around
        stmt = (
            select(User)
            .where(User.is_active.is_(True))
            .where(
                (User.preferred_time >= window_start) |
                (User.preferred_time < window_end)
            )
        )
    else:
        stmt = (
            select(User)
            .where(User.is_active.is_(True))
            .where(User.preferred_time >= window_start)
            .where(User.preferred_time < window_end)
        )

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def generate_user_digest(user_id: UUID) -> bool:
    """
    Generate a digest for a single user.

    Args:
        user_id: User's unique identifier.

    Returns:
        bool: True if successful, False otherwise.
    """
    session_maker = get_async_session_maker()
    async with session_maker() as db:
        try:
            digest_service = DigestService(db)
            digest = await digest_service.generate_digest(
                user_id=user_id,
                force=False,
            )
            await db.commit()

            logger.info(
                f"Generated scheduled digest for user {user_id}: "
                f"{digest.digest_date}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to generate digest for user {user_id}: {e}"
            )
            await db.rollback()
            return False


async def process_digest_generation() -> None:
    """
    Main job function to process digest generation for due users.

    This runs every N minutes (configured by digest_check_interval_minutes)
    and generates digests for users whose preferred time falls within
    the current window.
    """
    settings = get_settings()
    logger.debug("Starting digest generation check")
    current_time = datetime.now(timezone.utc)

    session_maker = get_async_session_maker()
    async with session_maker() as db:
        try:
            # Get users due for digest
            users = await get_users_due_for_digest(
                db=db,
                current_time_utc=current_time,
                window_minutes=settings.digest_check_interval_minutes,
            )

            if not users:
                logger.debug("No users due for digest generation")
                return

            logger.info(f"Found {len(users)} users due for digest generation")

            # Generate digests for each user
            success_count = 0
            for user in users:
                # Check if user has interests
                interest_service = InterestService(db)
                interests = await interest_service.get_user_interests(user.id)

                if not interests:
                    logger.debug(
                        f"Skipping user {user.id}: no interests selected"
                    )
                    continue

                success = await generate_user_digest(user.id)
                if success:
                    success_count += 1

            logger.info(
                f"Digest generation complete: "
                f"{success_count}/{len(users)} successful"
            )

        except Exception as e:
            logger.error(f"Digest generation job failed: {e}")


def digest_generation_job() -> None:
    """
    Wrapper for the async digest generation job.

    APScheduler calls this synchronously, so we need to run
    the async function in the event loop.
    """
    asyncio.create_task(process_digest_generation())


def schedule_digest_jobs() -> None:
    """
    Register all scheduled jobs with the scheduler.

    Called during scheduler startup.
    """
    settings = get_settings()
    # Digest generation job - runs every N minutes
    scheduler.add_job(
        digest_generation_job,
        trigger="interval",
        minutes=settings.digest_check_interval_minutes,
        id="digest_generation",
        name="Generate digests for due users",
        replace_existing=True,
    )

    logger.info(
        f"Scheduled digest generation job: "
        f"every {settings.digest_check_interval_minutes} minutes"
    )


async def seed_interests_on_startup() -> None:
    """
    Seed predefined interests on application startup.
    """
    session_maker = get_async_session_maker()
    async with session_maker() as db:
        try:
            interest_service = InterestService(db)
            created = await interest_service.seed_interests()
            await db.commit()

            if created > 0:
                logger.info(f"Seeded {created} interests on startup")

        except Exception as e:
            logger.error(f"Failed to seed interests: {e}")
            await db.rollback()
