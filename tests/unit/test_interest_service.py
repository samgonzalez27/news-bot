"""
Unit tests for interest_service.py.

Tests interest management functions with mocked database.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.services.interest_service import InterestService
from src.exceptions import NotFoundError


class TestGetAllInterests:
    """Tests for get_all_interests method."""

    @pytest.mark.asyncio
    async def test_get_all_interests_active_only(self):
        """Should return only active interests by default."""
        mock_interest = MagicMock()
        mock_interest.slug = "technology"
        mock_interest.is_active = True
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_interest]
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        service = InterestService(mock_db)
        interests = await service.get_all_interests()
        
        assert len(interests) == 1
        assert interests[0].slug == "technology"

    @pytest.mark.asyncio
    async def test_get_all_interests_include_inactive(self):
        """Should return all interests when active_only=False."""
        mock_active = MagicMock()
        mock_active.is_active = True
        mock_inactive = MagicMock()
        mock_inactive.is_active = False
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_active, mock_inactive]
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        service = InterestService(mock_db)
        interests = await service.get_all_interests(active_only=False)
        
        assert len(interests) == 2


class TestGetBySlug:
    """Tests for get_by_slug method."""

    @pytest.mark.asyncio
    async def test_get_by_slug_found(self):
        """Should return interest when found."""
        mock_interest = MagicMock()
        mock_interest.slug = "technology"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_interest
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        service = InterestService(mock_db)
        interest = await service.get_by_slug("technology")
        
        assert interest == mock_interest

    @pytest.mark.asyncio
    async def test_get_by_slug_not_found(self):
        """Should return None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        service = InterestService(mock_db)
        interest = await service.get_by_slug("nonexistent")
        
        assert interest is None


class TestGetBySlUgs:
    """Tests for get_by_slugs method."""

    @pytest.mark.asyncio
    async def test_get_by_slugs(self):
        """Should return interests matching slugs."""
        mock_tech = MagicMock()
        mock_tech.slug = "technology"
        mock_sports = MagicMock()
        mock_sports.slug = "sports"
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_tech, mock_sports]
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        service = InterestService(mock_db)
        interests = await service.get_by_slugs(["technology", "sports"])
        
        assert len(interests) == 2


class TestGetUserInterests:
    """Tests for get_user_interests method."""

    @pytest.mark.asyncio
    async def test_get_user_interests(self):
        """Should return user's interests."""
        user_id = uuid4()
        mock_interest = MagicMock()
        mock_interest.slug = "technology"
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_interest]
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        service = InterestService(mock_db)
        interests = await service.get_user_interests(user_id)
        
        assert len(interests) == 1


class TestUpdateUserInterests:
    """Tests for update_user_interests method."""

    @pytest.mark.asyncio
    async def test_update_user_interests_user_not_found(self):
        """Should raise NotFoundError when user not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        service = InterestService(mock_db)
        
        with pytest.raises(NotFoundError):
            await service.update_user_interests(uuid4(), ["technology"])

    @pytest.mark.asyncio
    async def test_update_user_interests_missing_slug(self):
        """Should raise NotFoundError for missing interest slug."""
        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = user_id
        
        # First call returns user
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_user_result
        
        service = InterestService(mock_db)
        
        # Mock get_by_slugs to return empty list (no interests found)
        with patch.object(service, "get_by_slugs", return_value=[]):
            with pytest.raises(NotFoundError):
                await service.update_user_interests(user_id, ["nonexistent"])

    @pytest.mark.asyncio
    async def test_update_user_interests_success(self):
        """Should update user interests successfully."""
        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = user_id
        
        mock_interest = MagicMock()
        mock_interest.id = uuid4()
        mock_interest.slug = "technology"
        
        # First call returns user
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_user_result
        mock_db.flush = AsyncMock()
        
        service = InterestService(mock_db)
        
        with patch.object(service, "get_by_slugs", return_value=[mock_interest]):
            result = await service.update_user_interests(user_id, ["technology"])
        
        assert len(result) == 1
        assert result[0].slug == "technology"


class TestAddInterestToUser:
    """Tests for add_interest_to_user method."""

    @pytest.mark.asyncio
    async def test_add_interest_not_found(self):
        """Should raise NotFoundError when interest not found."""
        mock_db = AsyncMock()
        
        service = InterestService(mock_db)
        
        with patch.object(service, "get_by_slug", return_value=None):
            with pytest.raises(NotFoundError):
                await service.add_interest_to_user(uuid4(), "nonexistent")

    @pytest.mark.asyncio
    async def test_add_interest_already_exists(self):
        """Should return interest if already subscribed."""
        user_id = uuid4()
        interest_id = uuid4()
        
        mock_interest = MagicMock()
        mock_interest.id = interest_id
        mock_interest.slug = "technology"
        
        mock_existing = MagicMock()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        service = InterestService(mock_db)
        
        with patch.object(service, "get_by_slug", return_value=mock_interest):
            result = await service.add_interest_to_user(user_id, "technology")
        
        assert result == mock_interest

    @pytest.mark.asyncio
    async def test_add_interest_success(self):
        """Should add interest successfully."""
        user_id = uuid4()
        interest_id = uuid4()
        
        mock_interest = MagicMock()
        mock_interest.id = interest_id
        mock_interest.slug = "technology"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # Not already subscribed
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        mock_db.flush = AsyncMock()
        
        service = InterestService(mock_db)
        
        with patch.object(service, "get_by_slug", return_value=mock_interest):
            result = await service.add_interest_to_user(user_id, "technology")
        
        assert result == mock_interest
        mock_db.add.assert_called_once()


class TestRemoveInterestFromUser:
    """Tests for remove_interest_from_user method."""

    @pytest.mark.asyncio
    async def test_remove_interest_not_found(self):
        """Should raise NotFoundError when interest not found."""
        mock_db = AsyncMock()
        
        service = InterestService(mock_db)
        
        with patch.object(service, "get_by_slug", return_value=None):
            with pytest.raises(NotFoundError):
                await service.remove_interest_from_user(uuid4(), "nonexistent")

    @pytest.mark.asyncio
    async def test_remove_interest_success(self):
        """Should remove interest successfully."""
        user_id = uuid4()
        interest_id = uuid4()
        
        mock_interest = MagicMock()
        mock_interest.id = interest_id
        mock_interest.slug = "technology"
        
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.flush = AsyncMock()
        
        service = InterestService(mock_db)
        
        with patch.object(service, "get_by_slug", return_value=mock_interest):
            await service.remove_interest_from_user(user_id, "technology")
        
        # Should have executed delete statement
        assert mock_db.execute.called


class TestSeedInterests:
    """Tests for seed_interests method."""

    @pytest.mark.asyncio
    async def test_seed_interests_all_new(self):
        """Should create all interests when none exist."""
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        
        service = InterestService(mock_db)
        
        # No existing interests
        with patch.object(service, "get_by_slug", return_value=None):
            with patch("src.services.interest_service.PREDEFINED_INTERESTS", [
                {"slug": "technology", "name": "Technology", "display_order": 1},
                {"slug": "sports", "name": "Sports", "display_order": 2},
            ]):
                count = await service.seed_interests()
        
        assert count == 2
        assert mock_db.add.call_count == 2

    @pytest.mark.asyncio
    async def test_seed_interests_some_exist(self):
        """Should only create new interests."""
        mock_existing = MagicMock()
        mock_existing.slug = "technology"
        
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        
        service = InterestService(mock_db)
        
        # First interest exists, second doesn't
        with patch.object(service, "get_by_slug", side_effect=[mock_existing, None]):
            with patch("src.services.interest_service.PREDEFINED_INTERESTS", [
                {"slug": "technology", "name": "Technology", "display_order": 1},
                {"slug": "sports", "name": "Sports", "display_order": 2},
            ]):
                count = await service.seed_interests()
        
        assert count == 1
        assert mock_db.add.call_count == 1
