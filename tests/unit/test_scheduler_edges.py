"""
Tests for scheduler edge cases and job execution.

Coverage improvements:
- Scheduler start/stop behavior
- Job registration
- User digest window calculation
- Digest generation error handling
- Interest seeding
"""

import pytest
from datetime import datetime, time, timedelta, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from src.scheduler.scheduler import start_scheduler, stop_scheduler, scheduler
from src.scheduler.jobs import (
    get_users_due_for_digest,
    generate_user_digest,
    process_digest_generation,
    digest_generation_job,
    schedule_digest_jobs,
    seed_interests_on_startup,
)


class TestSchedulerLifecycle:
    """Tests for scheduler start/stop behavior."""

    def test_start_scheduler_when_disabled(self):
        """Should not start scheduler when disabled."""
        with patch("src.scheduler.scheduler.get_settings") as mock_settings:
            mock_settings.return_value.scheduler_enabled = False
            
            # Ensure scheduler is not running
            if scheduler.running:
                scheduler.shutdown(wait=False)
            
            start_scheduler()
            
            # Should not be running
            assert not scheduler.running

    def test_stop_scheduler_when_not_running(self):
        """Should handle stopping when not running."""
        # Ensure scheduler is not running
        if scheduler.running:
            scheduler.shutdown(wait=False)
        
        # Should not raise
        stop_scheduler()


class TestGetUsersDueForDigest:
    """Tests for user digest window calculation."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_users(self):
        """Should return empty list when no users match."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        current_time = datetime.now(timezone.utc)
        users = await get_users_due_for_digest(mock_db, current_time)
        
        assert users == []

    @pytest.mark.asyncio
    async def test_accepts_window_minutes_parameter(self):
        """Should accept custom window minutes."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        current_time = datetime.now(timezone.utc)
        users = await get_users_due_for_digest(
            mock_db, 
            current_time,
            window_minutes=30,
        )
        
        assert users == []

    @pytest.mark.asyncio
    async def test_handles_midnight_crossing(self):
        """Should handle time window crossing midnight."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        # Time near midnight
        current_time = datetime(2024, 1, 1, 23, 50, tzinfo=timezone.utc)
        users = await get_users_due_for_digest(
            mock_db, 
            current_time,
            window_minutes=30,  # Will cross midnight
        )
        
        # Should execute without error
        mock_db.execute.assert_called_once()


class TestGenerateUserDigest:
    """Tests for individual user digest generation."""

    @pytest.mark.asyncio
    async def test_generates_digest_for_user(self):
        """Should generate digest for valid user."""
        user_id = uuid4()
        
        mock_session = AsyncMock()
        mock_session_maker = MagicMock(return_value=mock_session)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        mock_digest = MagicMock()
        mock_digest.digest_date = "2024-01-01"
        
        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.DigestService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service.generate_digest.return_value = mock_digest
                mock_service_class.return_value = mock_service
                
                result = await generate_user_digest(user_id)
                
                assert result is True
                mock_service.generate_digest.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_on_error(self):
        """Should return False when generation fails."""
        user_id = uuid4()
        
        mock_session = AsyncMock()
        mock_session_maker = MagicMock(return_value=mock_session)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.DigestService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service.generate_digest.side_effect = Exception("DB error")
                mock_service_class.return_value = mock_service
                
                result = await generate_user_digest(user_id)
                
                assert result is False
                mock_session.rollback.assert_called_once()


class TestProcessDigestGeneration:
    """Tests for main digest generation job."""

    @pytest.mark.asyncio
    async def test_logs_when_no_users_due(self):
        """Should log when no users are due."""
        mock_session = AsyncMock()
        mock_session_maker = MagicMock(return_value=mock_session)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.get_users_due_for_digest") as mock_get_users:
                mock_get_users.return_value = []
                
                await process_digest_generation()
                
                mock_get_users.assert_called_once()

    @pytest.mark.asyncio
    async def test_generates_for_users_with_interests(self):
        """Should generate digests for users with interests."""
        mock_user = MagicMock()
        mock_user.id = uuid4()
        
        mock_session = AsyncMock()
        mock_session_maker = MagicMock(return_value=mock_session)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.get_users_due_for_digest") as mock_get_users:
                mock_get_users.return_value = [mock_user]
                
                with patch("src.scheduler.jobs.InterestService") as mock_interest_class:
                    mock_interest_service = AsyncMock()
                    mock_interest_service.get_user_interests.return_value = [MagicMock()]
                    mock_interest_class.return_value = mock_interest_service
                    
                    with patch("src.scheduler.jobs.generate_user_digest") as mock_generate:
                        mock_generate.return_value = True
                        
                        await process_digest_generation()
                        
                        mock_generate.assert_called_once_with(mock_user.id)

    @pytest.mark.asyncio
    async def test_skips_users_without_interests(self):
        """Should skip users without interests."""
        mock_user = MagicMock()
        mock_user.id = uuid4()
        
        mock_session = AsyncMock()
        mock_session_maker = MagicMock(return_value=mock_session)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.get_users_due_for_digest") as mock_get_users:
                mock_get_users.return_value = [mock_user]
                
                with patch("src.scheduler.jobs.InterestService") as mock_interest_class:
                    mock_interest_service = AsyncMock()
                    mock_interest_service.get_user_interests.return_value = []  # No interests
                    mock_interest_class.return_value = mock_interest_service
                    
                    with patch("src.scheduler.jobs.generate_user_digest") as mock_generate:
                        await process_digest_generation()
                        
                        # Should not be called - user has no interests
                        mock_generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_job_error(self):
        """Should handle errors during job execution."""
        mock_session = AsyncMock()
        mock_session_maker = MagicMock(return_value=mock_session)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.get_users_due_for_digest") as mock_get_users:
                mock_get_users.side_effect = Exception("Database error")
                
                # Should not raise
                await process_digest_generation()


class TestDigestGenerationJobWrapper:
    """Tests for the sync wrapper function."""

    def test_creates_async_task(self):
        """Should create an async task."""
        with patch("src.scheduler.jobs.process_digest_generation") as mock_process:
            mock_process.return_value = None  # Prevent coroutine creation
            with patch("asyncio.create_task") as mock_create_task:
                digest_generation_job()
                mock_create_task.assert_called_once()


class TestScheduleDigestJobs:
    """Tests for job registration."""

    def test_adds_job_to_scheduler(self):
        """Should add digest generation job to scheduler."""
        with patch("src.scheduler.jobs.get_settings") as mock_settings:
            mock_settings.return_value.digest_check_interval_minutes = 15
            
            with patch.object(scheduler, "add_job") as mock_add_job:
                schedule_digest_jobs()
                
                mock_add_job.assert_called_once()
                call_kwargs = mock_add_job.call_args[1]
                assert call_kwargs["id"] == "digest_generation"
                assert call_kwargs["minutes"] == 15
                
                # Verify the func argument is the sync wrapper
                call_args = mock_add_job.call_args[0]
                assert call_args[0] == digest_generation_job


class TestSeedInterestsOnStartup:
    """Tests for interest seeding."""

    @pytest.mark.asyncio
    async def test_seeds_interests(self):
        """Should seed interests via interest service."""
        mock_session = AsyncMock()
        mock_session_maker = MagicMock(return_value=mock_session)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.InterestService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service.seed_interests.return_value = 5
                mock_service_class.return_value = mock_service
                
                await seed_interests_on_startup()
                
                mock_service.seed_interests.assert_called_once()
                mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_seeding_error(self):
        """Should handle errors during seeding."""
        mock_session = AsyncMock()
        mock_session_maker = MagicMock(return_value=mock_session)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.InterestService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service.seed_interests.side_effect = Exception("DB error")
                mock_service_class.return_value = mock_service
                
                # Should not raise
                await seed_interests_on_startup()
                
                mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_logs_when_interests_created(self):
        """Should log when interests are created."""
        mock_session = AsyncMock()
        mock_session_maker = MagicMock(return_value=mock_session)
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.InterestService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service.seed_interests.return_value = 8
                mock_service_class.return_value = mock_service
                
                with patch("src.scheduler.jobs.logger") as mock_logger:
                    await seed_interests_on_startup()
                    
                    # Should log info about seeded interests
                    mock_logger.info.assert_called()


class TestSchedulerModule:
    """Tests for scheduler module configuration."""

    def test_scheduler_has_job_defaults(self):
        """Scheduler should have job defaults configured."""
        from src.scheduler.scheduler import job_defaults
        
        assert "coalesce" in job_defaults
        assert "max_instances" in job_defaults
        assert "misfire_grace_time" in job_defaults

    def test_scheduler_timezone_is_utc(self):
        """Scheduler should use UTC timezone."""
        # scheduler.timezone could be a string or timezone object
        tz = scheduler.timezone
        if hasattr(tz, 'zone'):
            assert tz.zone == "UTC"
        else:
            # Could be datetime.timezone or string
            assert str(tz) in ["UTC", "utc", "datetime.timezone.utc"]
