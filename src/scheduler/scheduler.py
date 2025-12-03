"""
APScheduler configuration and lifecycle management.

This module configures APScheduler for the daily digest generation system.
The scheduler runs as an embedded worker within the FastAPI process.

Architecture:
-------------
- Uses AsyncIOScheduler for async job execution
- MemoryJobStore: Jobs are defined in code, not persisted
- Single worker instance: Only one API container should run the scheduler
- UTC timezone: All time comparisons are done in UTC

Job Execution Model:
--------------------
- coalesce=True: If multiple runs are missed, only run once
- max_instances=1: Prevent concurrent runs of the same job
- misfire_grace_time=300s: Allow 5 minutes of delay before skipping

Production Considerations:
--------------------------
- In multi-container deployments, set SCHEDULER_ENABLED=false on all
  but one container to prevent duplicate job execution
- The scheduler is not distributed; it runs in a single process
- Job state is lost on restart (acceptable for interval jobs)
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from src.config import get_settings
from src.logging_config import get_logger

logger = get_logger("scheduler")

# Configure job stores and executors
jobstores = {
    "default": MemoryJobStore(),
}

# Use AsyncIOExecutor to run jobs in the main event loop
executors = {
    "default": AsyncIOExecutor(),
}

job_defaults = {
    "coalesce": True,  # Combine multiple missed runs into one
    "max_instances": 1,  # Only one instance of each job at a time
    "misfire_grace_time": 60 * 5,  # 5 minute grace period for late jobs
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
    settings = get_settings()
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
