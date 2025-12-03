"""
Scheduled job definitions for daily digest generation.

Architecture:
------------
The scheduler runs an interval job every N minutes (default: 15).
Each run checks which users have a preferred_time in the current window
and generates their daily digest if not already generated.

Key Concepts:
-------------
- digest_date: The date of the NEWS content (always yesterday in UTC)
- preferred_time: When the user wants to RECEIVE their digest (stored in UTC)
- Window matching: Users whose preferred_time falls in [now, now + interval)

Idempotency:
------------
Digest generation is idempotent per (user_id, digest_date). If a user
clicks "Generate Now" before their scheduled time, the scheduler will
see the digest already exists and skip generation (not an error).

Edge Cases Handled:
-------------------
1. Midnight crossing: Window from 23:50 to 00:05 handled via OR query
2. Manual generation: "Generate Now" creates same digest, scheduler skips
3. Missed windows: Users who miss their window don't get duplicate attempts
4. Server restart: Only current window is checked, no backfill
"""

import asyncio
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import get_async_session_maker
from src.logging_config import get_logger
from src.models.digest import Digest, DigestStatus
from src.models.user import User
from src.scheduler.scheduler import scheduler
from src.services.digest_service import DigestService
from src.services.interest_service import InterestService

logger = get_logger("scheduler_jobs")


def compute_digest_date() -> date:
    """
    Compute the digest_date for current scheduled generation.

    The digest contains YESTERDAY's news because:
    1. NewsAPI free tier returns previous day's headlines
    2. A "morning digest" summarizes what happened yesterday

    Returns:
        date: Yesterday's date in UTC.
    """
    return date.today() - timedelta(days=1)


def compute_time_window(
    current_time_utc: datetime,
    window_minutes: int,
) -> Tuple[time, time, bool]:
    """
    Compute the time window for user eligibility.

    Args:
        current_time_utc: Current UTC datetime.
        window_minutes: Size of window in minutes.

    Returns:
        Tuple of (window_start, window_end, crosses_midnight).
    """
    window_start = current_time_utc.time()
    window_end_dt = current_time_utc + timedelta(minutes=window_minutes)
    window_end = window_end_dt.time()

    # Check if window crosses midnight (e.g., 23:50 -> 00:05)
    crosses_midnight = window_end < window_start

    return window_start, window_end, crosses_midnight


async def get_users_due_for_digest(
    db: AsyncSession,
    current_time_utc: datetime,
    window_minutes: int = 15,
) -> List[User]:
    """
    Get active users whose preferred_time falls within the current window.

    The query finds users where:
    - User is active (is_active = True)
    - User's preferred_time is in [window_start, window_end)

    For midnight-crossing windows (e.g., 23:50-00:05), uses OR logic:
    - preferred_time >= 23:50 OR preferred_time < 00:05

    Args:
        db: Database session.
        current_time_utc: Current UTC datetime (must be timezone-aware).
        window_minutes: Size of the time window to check.

    Returns:
        List of User objects eligible for digest generation.
    """
    window_start, window_end, crosses_midnight = compute_time_window(
        current_time_utc, window_minutes
    )

    logger.debug(
        f"Checking time window: {window_start.isoformat()} - "
        f"{window_end.isoformat()} (crosses_midnight={crosses_midnight})"
    )

    if crosses_midnight:
        # Window crosses midnight: match times >= start OR < end
        # Example: 23:50-00:05 matches 23:50, 23:55, 00:00, 00:04
        time_condition = or_(
            User.preferred_time >= window_start,
            User.preferred_time < window_end,
        )
    else:
        # Normal window: match times >= start AND < end
        # Example: 08:00-08:15 matches 08:00, 08:05, 08:10, 08:14
        time_condition = and_(
            User.preferred_time >= window_start,
            User.preferred_time < window_end,
        )

    stmt = (
        select(User)
        .where(User.is_active.is_(True))
        .where(time_condition)
    )

    result = await db.execute(stmt)
    users = list(result.scalars().all())

    logger.debug(f"Found {len(users)} users in time window")
    return users


async def check_digest_exists(
    db: AsyncSession,
    user_id: UUID,
    digest_date: date,
) -> bool:
    """
    Check if a completed digest already exists for user on given date.

    Args:
        db: Database session.
        user_id: User's unique identifier.
        digest_date: Date to check.

    Returns:
        True if a completed digest exists, False otherwise.
    """
    stmt = select(Digest.id).where(
        Digest.user_id == user_id,
        Digest.digest_date == digest_date,
        Digest.status == DigestStatus.COMPLETED.value,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def generate_user_digest(
    user_id: UUID,
    user_email: str,
    digest_date: date,
) -> Tuple[bool, str]:
    """
    Generate a digest for a single user.

    Uses a separate database session to isolate failures.
    The digest_date is explicitly passed to ensure consistency
    across all users processed in the same batch.

    Args:
        user_id: User's unique identifier.
        user_email: User's email (for logging).
        digest_date: The date of news content to include.

    Returns:
        Tuple of (success: bool, message: str).
    """
    session_maker = get_async_session_maker()
    async with session_maker() as db:
        try:
            digest_service = DigestService(db)
            digest = await digest_service.generate_digest(
                user_id=user_id,
                digest_date=digest_date,
                force=False,  # Never force - respect existing digests
            )
            await db.commit()

            # Check if this was a new generation or existing
            # (DigestService returns existing if already present)
            return True, f"digest_date={digest.digest_date}"

        except Exception as e:
            logger.error(
                f"Failed to generate digest for user {user_email} "
                f"({user_id}): {e}",
                exc_info=True,
            )
            await db.rollback()
            return False, str(e)


async def process_digest_generation() -> None:
    """
    Main scheduled job: generate digests for users due in current window.

    This function is called every N minutes by APScheduler. It:
    1. Computes the current time window
    2. Finds users whose preferred_time falls in the window
    3. Skips users without interests
    4. Generates digests (idempotent - skips if already exists)

    The digest_date is computed ONCE at the start of the batch to ensure
    all users in the same run get the same date, even if processing
    spans midnight.

    Logging:
    --------
    - INFO: Job start/end with summary stats
    - DEBUG: Per-user details
    - ERROR: Failures with stack traces
    """
    settings = get_settings()
    current_time = datetime.now(timezone.utc)
    digest_date = compute_digest_date()

    logger.info(
        f"[SCHEDULER] Starting digest generation check | "
        f"time={current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC | "
        f"digest_date={digest_date} | "
        f"window={settings.digest_check_interval_minutes}min"
    )

    session_maker = get_async_session_maker()
    async with session_maker() as db:
        try:
            # Step 1: Find users in current time window
            users = await get_users_due_for_digest(
                db=db,
                current_time_utc=current_time,
                window_minutes=settings.digest_check_interval_minutes,
            )

            if not users:
                logger.info("[SCHEDULER] No users due for digest generation")
                return

            logger.info(
                f"[SCHEDULER] Found {len(users)} users in time window"
            )

            # Step 2: Process each user
            stats = {
                "total": len(users),
                "generated": 0,
                "skipped_no_interests": 0,
                "skipped_exists": 0,
                "failed": 0,
            }

            for user in users:
                # Check interests first (cheaper than digest generation)
                interest_service = InterestService(db)
                interests = await interest_service.get_user_interests(user.id)

                if not interests:
                    logger.debug(
                        f"[SCHEDULER] Skipping user {user.email}: "
                        f"no interests selected"
                    )
                    stats["skipped_no_interests"] += 1
                    continue

                # Check if digest already exists (e.g., from "Generate Now")
                exists = await check_digest_exists(db, user.id, digest_date)
                if exists:
                    logger.debug(
                        f"[SCHEDULER] Skipping user {user.email}: "
                        f"digest already exists for {digest_date}"
                    )
                    stats["skipped_exists"] += 1
                    continue

                # Generate the digest
                success, message = await generate_user_digest(
                    user_id=user.id,
                    user_email=user.email,
                    digest_date=digest_date,
                )

                if success:
                    logger.info(
                        f"[SCHEDULER] Generated digest for {user.email}: "
                        f"{message}"
                    )
                    stats["generated"] += 1
                else:
                    stats["failed"] += 1

            # Step 3: Log summary
            logger.info(
                f"[SCHEDULER] Digest generation complete | "
                f"total={stats['total']} | "
                f"generated={stats['generated']} | "
                f"skipped_exists={stats['skipped_exists']} | "
                f"skipped_no_interests={stats['skipped_no_interests']} | "
                f"failed={stats['failed']}"
            )

        except Exception as e:
            logger.error(
                f"[SCHEDULER] Digest generation job failed: {e}",
                exc_info=True,
            )


def digest_generation_job() -> None:
    """
    Synchronous wrapper for the async digest generation job.

    APScheduler calls job functions synchronously. This wrapper
    creates an async task in the running event loop.

    Note: Uses create_task() because the scheduler runs in an
    AsyncIO context (FastAPI's event loop).
    """
    asyncio.create_task(process_digest_generation())


def schedule_digest_jobs() -> None:
    """
    Register all scheduled jobs with the scheduler.

    Called during scheduler startup. Registers:
    - digest_generation: Runs every N minutes to check for due users

    The job uses replace_existing=True to handle server restarts
    gracefully (re-registers the job without duplicates).
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
        f"[SCHEDULER] Registered digest generation job: "
        f"every {settings.digest_check_interval_minutes} minutes"
    )

    # Run immediately on startup to catch any users who might have
    # been missed if the server was down during their preferred time
    # This is safe because generation is idempotent
    logger.info("[SCHEDULER] Running initial digest check on startup")
    asyncio.create_task(process_digest_generation())


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
