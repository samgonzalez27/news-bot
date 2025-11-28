"""
APScheduler configuration and lifecycle management.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from src.config import get_settings
from src.logging_config import get_logger

logger = get_logger("scheduler")
settings = get_settings()

# Configure job stores and executors
jobstores = {
    "default": MemoryJobStore(),
}

executors = {
    "default": AsyncIOExecutor(),
}

job_defaults = {
    "coalesce": True,  # Combine multiple missed runs into one
    "max_instances": 1,  # Only one instance of each job at a time
    "misfire_grace_time": 60 * 5,  # 5 minute grace period
}

# Create scheduler instance
scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone="UTC",
)


def start_scheduler() -> None:
    """
    Start the APScheduler.

    Should be called during application startup.
    """
    if not settings.scheduler_enabled:
        logger.info("Scheduler is disabled by configuration")
        return

    if scheduler.running:
        logger.warning("Scheduler is already running")
        return

    # Import and register jobs
    from src.scheduler.jobs import schedule_digest_jobs
    schedule_digest_jobs()

    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler() -> None:
    """
    Stop the APScheduler.

    Should be called during application shutdown.
    """
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")
