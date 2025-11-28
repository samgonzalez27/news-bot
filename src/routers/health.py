"""
Health check endpoints for monitoring and observability.

Provides endpoints for:
- Basic health check
- Database connectivity check
- Scheduler status check
"""

import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import get_db
from src.logging_config import get_logger
from src.scheduler.scheduler import scheduler

logger = get_logger("health")
router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    summary="Basic health check",
    description="Returns basic health status of the API.",
    response_model=Dict[str, Any],
)
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns application status and basic info.
    Used by Docker healthcheck and load balancers.
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "1.0.0",
        "environment": settings.app_env,
    }


@router.get(
    "/db",
    summary="Database health check",
    description="Checks database connectivity and returns latency.",
    response_model=Dict[str, Any],
)
async def health_check_db(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Database health check endpoint.
    
    Performs a simple query to verify database connectivity
    and measures response latency.
    """
    start_time = time.perf_counter()
    
    try:
        # Execute simple query to check connectivity
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        return {
            "status": "ok",
            "latency_ms": round(latency_ms, 2),
        }
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.error(f"Database health check failed: {e}")
        
        return {
            "status": "error",
            "latency_ms": round(latency_ms, 2),
            "error": str(e),
        }


@router.get(
    "/scheduler",
    summary="Scheduler health check",
    description="Returns scheduler status and job information.",
    response_model=Dict[str, Any],
)
async def health_check_scheduler() -> Dict[str, Any]:
    """
    Scheduler health check endpoint.
    
    Returns information about the scheduler including:
    - Whether it's enabled
    - Running status
    - Loaded jobs and their next run times
    """
    settings = get_settings()
    
    # Base response
    response: Dict[str, Any] = {
        "enabled": settings.scheduler_enabled,
        "running": scheduler.running if settings.scheduler_enabled else False,
    }
    
    # Add job information if scheduler is enabled
    if settings.scheduler_enabled and scheduler.running:
        jobs: List[Dict[str, Any]] = []
        
        for job in scheduler.get_jobs():
            job_info: Dict[str, Optional[str]] = {
                "id": job.id,
                "name": job.name,
                "next_run_time": (
                    job.next_run_time.isoformat() if job.next_run_time else None
                ),
            }
            jobs.append(job_info)
        
        response["jobs"] = jobs
        response["job_count"] = len(jobs)
    else:
        response["jobs"] = []
        response["job_count"] = 0
    
    return response


@router.get(
    "/ready",
    summary="Readiness check",
    description="Checks if the application is ready to serve traffic.",
    response_model=Dict[str, Any],
)
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Readiness check endpoint for Kubernetes/orchestration.
    
    Verifies all critical dependencies are available:
    - Database connectivity
    - Scheduler running (if enabled)
    """
    settings = get_settings()
    checks: Dict[str, bool] = {}
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False
    
    # Check scheduler
    if settings.scheduler_enabled:
        checks["scheduler"] = scheduler.running
    else:
        checks["scheduler"] = True  # Not required if disabled
    
    # Overall status
    all_healthy = all(checks.values())
    
    return {
        "ready": all_healthy,
        "checks": checks,
    }


@router.get(
    "/live",
    summary="Liveness check",
    description="Simple liveness probe for orchestration.",
    response_model=Dict[str, str],
)
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint for Kubernetes/orchestration.
    
    Simple endpoint that returns OK if the process is alive.
    Does not check dependencies - that's what readiness is for.
    """
    return {"status": "alive"}
