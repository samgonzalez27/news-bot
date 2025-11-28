"""
Unit tests for user_service.py.

Tests user management functions with mocked database.
"""

import pytest
from datetime import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.services.user_service import UserService
from src.schemas.user import UserCreate, UserUpdate, UserPreferencesUpdate
from src.exceptions import DuplicateError, NotFoundError


class TestCreateUser:
    """Tests for create_user method."""

    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Should create user successfully."""
        mock_db = AsyncMock()
        
        # No existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        service = UserService(mock_db)
        
        user_data = UserCreate(
            email="test@example.com",
            password="SecurePass123",
            full_name="Test User",
            preferred_time="08:00",
            timezone="UTC",
        )
        
        with patch.object(service, "get_by_email", return_value=None):
            # Mock the flush and refresh
            mock_db.flush = AsyncMock()
            mock_db.refresh = AsyncMock()
            
            user = await service.create_user(user_data)
        
        assert user.email == "test@example.com"
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self):
        """Should raise DuplicateError for existing email."""
        mock_db = AsyncMock()
        
        existing_user = MagicMock()
        existing_user.email = "test@example.com"
        
        service = UserService(mock_db)
        
        user_data = UserCreate(
            email="test@example.com",
            password="SecurePass123",
            full_name="Test User",
            preferred_time="08:00",
            timezone="UTC",
        )
        
        with patch.object(service, "get_by_email", return_value=existing_user):
            with pytest.raises(DuplicateError):
                await service.create_user(user_data)


class TestGetById:
    """Tests for get_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self):
        """Should return user when found."""
        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = user_id
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        service = UserService(mock_db)
        user = await service.get_by_id(user_id)
        
        assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """Should return None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        service = UserService(mock_db)
        user = await service.get_by_id(uuid4())
        
        assert user is None


class TestGetByEmail:
    """Tests for get_by_email method."""

    @pytest.mark.asyncio
    async def test_get_by_email_found(self):
        """Should return user when found."""
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        service = UserService(mock_db)
        user = await service.get_by_email("test@example.com")
        
        assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self):
        """Should return None when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        service = UserService(mock_db)
        user = await service.get_by_email("nonexistent@example.com")
        
        assert user is None


class TestUpdateUser:
    """Tests for update_user method."""

    @pytest.mark.asyncio
    async def test_update_user_not_found(self):
        """Should raise NotFoundError when user not found."""
        mock_db = AsyncMock()
        
        service = UserService(mock_db)
        
        with patch.object(service, "get_by_id", return_value=None):
            with pytest.raises(NotFoundError):
                await service.update_user(
                    uuid4(),
                    UserUpdate(full_name="New Name"),
                )

    @pytest.mark.asyncio
    async def test_update_user_email_conflict(self):
        """Should raise DuplicateError when email already exists."""
        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.email = "original@example.com"
        
        existing_user = MagicMock()
        existing_user.email = "taken@example.com"
        
        mock_db = AsyncMock()
        
        service = UserService(mock_db)
        
        with patch.object(service, "get_by_id", return_value=mock_user):
            with patch.object(service, "get_by_email", return_value=existing_user):
                with pytest.raises(DuplicateError):
                    await service.update_user(
                        user_id,
                        UserUpdate(email="taken@example.com"),
                    )

    @pytest.mark.asyncio
    async def test_update_user_success(self):
        """Should update user successfully."""
        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user.full_name = "Old Name"
        
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        service = UserService(mock_db)
        
        with patch.object(service, "get_by_id", return_value=mock_user):
            result = await service.update_user(
                user_id,
                UserUpdate(full_name="New Name"),
            )
        
        assert result.full_name == "New Name"


class TestUpdatePreferences:
    """Tests for update_preferences method."""

    @pytest.mark.asyncio
    async def test_update_preferences_not_found(self):
        """Should raise NotFoundError when user not found."""
        mock_db = AsyncMock()
        
        service = UserService(mock_db)
        
        with patch.object(service, "get_by_id", return_value=None):
            with pytest.raises(NotFoundError):
                await service.update_preferences(
                    uuid4(),
                    UserPreferencesUpdate(preferred_time="09:00"),
                )

    @pytest.mark.asyncio
    async def test_update_preferences_success(self):
        """Should update preferences successfully."""
        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.preferred_time = time(8, 0)
        mock_user.timezone = "UTC"
        
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        service = UserService(mock_db)
        
        with patch.object(service, "get_by_id", return_value=mock_user):
            result = await service.update_preferences(
                user_id,
                UserPreferencesUpdate(preferred_time="18:30", timezone="America/New_York"),
            )
        
        assert result.preferred_time == time(18, 30)
        assert result.timezone == "America/New_York"


class TestDeactivateUser:
    """Tests for deactivate_user method."""

    @pytest.mark.asyncio
    async def test_deactivate_user_not_found(self):
        """Should raise NotFoundError when user not found."""
        mock_db = AsyncMock()
        
        service = UserService(mock_db)
        
        with patch.object(service, "get_by_id", return_value=None):
            with pytest.raises(NotFoundError):
                await service.deactivate_user(uuid4())

    @pytest.mark.asyncio
    async def test_deactivate_user_success(self):
        """Should deactivate user successfully."""
        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.is_active = True
        
        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()
        
        service = UserService(mock_db)
        
        with patch.object(service, "get_by_id", return_value=mock_user):
            result = await service.deactivate_user(user_id)
        
        assert result.is_active is False


class TestVerifyCredentials:
    """Tests for verify_credentials method."""

    @pytest.mark.asyncio
    async def test_verify_credentials_user_not_found(self):
        """Should return None when user not found."""
        mock_db = AsyncMock()
        
        service = UserService(mock_db)
        
        with patch.object(service, "get_by_email", return_value=None):
            result = await service.verify_credentials(
                "nonexistent@example.com",
                "password",
            )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_credentials_inactive_user(self):
        """Should return None for inactive user."""
        mock_user = MagicMock()
        mock_user.is_active = False
        
        mock_db = AsyncMock()
        
        service = UserService(mock_db)
        
        with patch.object(service, "get_by_email", return_value=mock_user):
            result = await service.verify_credentials(
                "test@example.com",
                "password",
            )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_credentials_wrong_password(self):
        """Should return None for wrong password."""
        mock_user = MagicMock()
        mock_user.is_active = True
        mock_user.hashed_password = "hashed"
        
        mock_db = AsyncMock()
        
        service = UserService(mock_db)
        
        with patch.object(service, "get_by_email", return_value=mock_user):
            with patch("src.services.user_service.AuthService.verify_password", return_value=False):
                result = await service.verify_credentials(
                    "test@example.com",
                    "wrongpassword",
                )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_credentials_success(self):
        """Should return user for valid credentials."""
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.hashed_password = "hashed"
        
        mock_db = AsyncMock()
        
        service = UserService(mock_db)
        
        with patch.object(service, "get_by_email", return_value=mock_user):
            with patch("src.services.user_service.AuthService.verify_password", return_value=True):
                result = await service.verify_credentials(
                    "test@example.com",
                    "correctpassword",
                )
        
        assert result == mock_user
