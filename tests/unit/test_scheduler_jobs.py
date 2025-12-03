"""
Unit tests for scheduler jobs.

Tests the job functions with mocked database sessions.
"""

import pytest
from datetime import date, datetime, time, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.scheduler.jobs import (
    compute_digest_date,
    compute_time_window,
    get_users_due_for_digest,
    generate_user_digest,
    check_digest_exists,
    process_digest_generation,
    seed_interests_on_startup,
)


class TestComputeDigestDate:
    """Tests for compute_digest_date function."""

    def test_returns_yesterday(self):
        """Should return yesterday's date."""
        result = compute_digest_date()
        expected = date.today() - timedelta(days=1)
        assert result == expected


class TestComputeTimeWindow:
    """Tests for compute_time_window function."""

    def test_normal_window(self):
        """Should compute window within same day."""
        current = datetime(2024, 1, 1, 8, 0, tzinfo=timezone.utc)
        start, end, crosses = compute_time_window(current, 15)
        
        assert start == time(8, 0)
        assert end == time(8, 15)
        assert crosses is False

    def test_midnight_crossing(self):
        """Should detect midnight crossing."""
        current = datetime(2024, 1, 1, 23, 50, tzinfo=timezone.utc)
        start, end, crosses = compute_time_window(current, 15)
        
        assert start == time(23, 50)
        assert end == time(0, 5)
        assert crosses is True


class TestGetUsersDueForDigest:
    """Tests for get_users_due_for_digest function."""

    @pytest.mark.asyncio
    async def test_returns_users_in_window(self):
        """Should return users whose preferred time is in window."""
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.preferred_time = time(8, 0)
        mock_user.is_active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_user]

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        current_time = datetime(2024, 1, 1, 8, 5, tzinfo=timezone.utc)

        users = await get_users_due_for_digest(mock_db, current_time, 15)

        assert mock_db.execute.called
        # Query was executed
        assert len(users) == 1
        assert users[0].id == mock_user.id

    @pytest.mark.asyncio
    async def test_handles_midnight_crossing(self):
        """Should handle time window crossing midnight."""
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.preferred_time = time(23, 55)
        mock_user.is_active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_user]

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        # Time near midnight
        current_time = datetime(2024, 1, 1, 23, 50, tzinfo=timezone.utc)

        users = await get_users_due_for_digest(mock_db, current_time, 15)

        assert mock_db.execute.called
        assert len(users) == 1

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_users(self):
        """Should return empty list when no users in window."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        current_time = datetime(2024, 1, 1, 3, 0, tzinfo=timezone.utc)

        users = await get_users_due_for_digest(mock_db, current_time, 15)

        assert users == []


class TestCheckDigestExists:
    """Tests for check_digest_exists function."""

    @pytest.mark.asyncio
    async def test_returns_true_when_exists(self):
        """Should return True when digest exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid4()

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await check_digest_exists(mock_db, uuid4(), date.today())
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_not_exists(self):
        """Should return False when digest doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await check_digest_exists(mock_db, uuid4(), date.today())
        assert result is False


class TestGenerateUserDigest:
    """Tests for generate_user_digest function."""

    @pytest.mark.asyncio
    async def test_successful_generation(self):
        """Should generate digest and return success tuple."""
        user_id = uuid4()
        user_email = "test@example.com"
        digest_date = date.today() - timedelta(days=1)
        
        mock_digest = MagicMock()
        mock_digest.digest_date = digest_date

        mock_db = AsyncMock()
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.DigestService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service.generate_digest.return_value = mock_digest
                mock_service_class.return_value = mock_service

                success, message = await generate_user_digest(user_id, user_email, digest_date)

        assert success is True
        assert "digest_date=" in message
        mock_service.generate_digest.assert_called_once_with(
            user_id=user_id,
            digest_date=digest_date,
            force=False,
        )
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_exception(self):
        """Should return failure tuple on exception."""
        user_id = uuid4()
        user_email = "test@example.com"
        digest_date = date.today() - timedelta(days=1)

        mock_db = AsyncMock()
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.DigestService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service.generate_digest.side_effect = Exception("Test error")
                mock_service_class.return_value = mock_service

                success, message = await generate_user_digest(user_id, user_email, digest_date)

        assert success is False
        assert "Test error" in message
        mock_db.rollback.assert_called_once()


class TestProcessDigestGeneration:
    """Tests for process_digest_generation function."""

    @pytest.mark.asyncio
    async def test_no_users_due(self):
        """Should handle case when no users are due."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.get_settings") as mock_settings:
                mock_settings.return_value.digest_check_interval_minutes = 15
                await process_digest_generation()

        # Should have called execute to query users
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_processes_users_with_interests(self):
        """Should process users who have interests."""
        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user.is_active = True

        mock_interest = MagicMock()
        mock_interest.slug = "technology"

        mock_db = AsyncMock()

        # First query for users
        mock_user_result = MagicMock()
        mock_user_result.scalars.return_value.all.return_value = [mock_user]
        
        # Second query for user interests
        mock_interest_result = MagicMock()
        mock_interest_result.scalars.return_value.all.return_value = [mock_interest]

        # Third query for digest exists check
        mock_exists_result = MagicMock()
        mock_exists_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_user_result, mock_interest_result, mock_exists_result]

        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.get_settings") as mock_settings:
                mock_settings.return_value.digest_check_interval_minutes = 15
                with patch("src.scheduler.jobs.generate_user_digest", return_value=(True, "ok")) as mock_gen:
                    await process_digest_generation()

        mock_gen.assert_called_once()
        call_args = mock_gen.call_args
        assert call_args.kwargs["user_id"] == user_id
        assert call_args.kwargs["user_email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_skips_users_without_interests(self):
        """Should skip users who have no interests."""
        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user.is_active = True

        mock_db = AsyncMock()

        # First query for users
        mock_user_result = MagicMock()
        mock_user_result.scalars.return_value.all.return_value = [mock_user]
        
        # Second query for user interests - empty
        mock_interest_result = MagicMock()
        mock_interest_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_user_result, mock_interest_result]

        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.get_settings") as mock_settings:
                mock_settings.return_value.digest_check_interval_minutes = 15
                with patch("src.scheduler.jobs.generate_user_digest") as mock_gen:
                    await process_digest_generation()

        # Should NOT have called generate since user has no interests
        mock_gen.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_users_with_existing_digest(self):
        """Should skip users who already have digest for today."""
        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user.is_active = True

        mock_interest = MagicMock()
        mock_interest.slug = "technology"

        mock_db = AsyncMock()

        # First query for users
        mock_user_result = MagicMock()
        mock_user_result.scalars.return_value.all.return_value = [mock_user]
        
        # Second query for user interests
        mock_interest_result = MagicMock()
        mock_interest_result.scalars.return_value.all.return_value = [mock_interest]

        # Third query for digest exists check - returns existing
        mock_exists_result = MagicMock()
        mock_exists_result.scalar_one_or_none.return_value = uuid4()

        mock_db.execute.side_effect = [mock_user_result, mock_interest_result, mock_exists_result]

        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.get_settings") as mock_settings:
                mock_settings.return_value.digest_check_interval_minutes = 15
                with patch("src.scheduler.jobs.generate_user_digest") as mock_gen:
                    await process_digest_generation()

        # Should NOT have called generate since digest already exists
        mock_gen.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_exception(self):
        """Should handle exceptions gracefully."""
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database error")

        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.get_settings") as mock_settings:
                mock_settings.return_value.digest_check_interval_minutes = 15
                # Should not raise
                await process_digest_generation()


class TestSeedInterestsOnStartup:
    """Tests for seed_interests_on_startup function."""

    @pytest.mark.asyncio
    async def test_seeds_interests_successfully(self):
        """Should seed interests on startup."""
        mock_db = AsyncMock()

        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.InterestService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service.seed_interests.return_value = 5
                mock_service_class.return_value = mock_service

                await seed_interests_on_startup()

        mock_service.seed_interests.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_exception(self):
        """Should handle exceptions during seeding."""
        mock_db = AsyncMock()

        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("src.scheduler.jobs.get_async_session_maker", return_value=mock_session_maker):
            with patch("src.scheduler.jobs.InterestService") as mock_service_class:
                mock_service = AsyncMock()
                mock_service.seed_interests.side_effect = Exception("Seed error")
                mock_service_class.return_value = mock_service

                # Should not raise
                await seed_interests_on_startup()

        mock_db.rollback.assert_called_once()
