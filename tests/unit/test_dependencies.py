"""
Unit tests for dependencies module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi.security import HTTPAuthorizationCredentials

from src.dependencies import (
    get_token_from_header,
    get_current_user_id,
    get_current_user,
    get_current_active_user,
)
from src.exceptions import AuthenticationError


class TestGetTokenFromHeader:
    """Tests for get_token_from_header function.
    
    Note: The HTTPBearer security scheme handles validation of the Authorization
    header format. These tests verify the token extraction from valid credentials.
    Invalid/missing headers are handled by HTTPBearer and return 401 via integration tests.
    """

    @pytest.mark.asyncio
    async def test_valid_bearer_token(self):
        """Should return token from valid credentials."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="mytoken123")
        
        token = await get_token_from_header(credentials)
        
        assert token == "mytoken123"

    @pytest.mark.asyncio
    async def test_extracts_credentials_attribute(self):
        """Should extract the credentials attribute from HTTPAuthorizationCredentials."""
        expected_token = "jwt.token.here"
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=expected_token)
        
        token = await get_token_from_header(credentials)
        
        assert token == expected_token

    @pytest.mark.asyncio
    async def test_handles_long_token(self):
        """Should handle long JWT tokens."""
        long_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." + "a" * 500
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=long_token)
        
        token = await get_token_from_header(credentials)
        
        assert token == long_token


class TestGetCurrentUserId:
    """Tests for get_current_user_id function."""

    @pytest.mark.asyncio
    async def test_extracts_user_id_from_token(self):
        """Should extract user ID from valid token."""
        user_id = uuid4()
        
        with patch("src.dependencies.AuthService.get_user_id_from_token", return_value=user_id):
            result = await get_current_user_id("valid_token")
        
        assert result == user_id


class TestGetCurrentUser:
    """Tests for get_current_user function."""

    @pytest.mark.asyncio
    async def test_user_not_found(self):
        """Should raise AuthenticationError when user not found."""
        user_id = uuid4()
        mock_db = AsyncMock()
        
        with patch("src.dependencies.UserService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_by_id.return_value = None
            mock_service_class.return_value = mock_service
            
            with pytest.raises(AuthenticationError) as exc_info:
                await get_current_user(user_id, mock_db)
            
            assert "User not found" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_user_inactive(self):
        """Should raise AuthenticationError when user is inactive."""
        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.is_active = False
        mock_db = AsyncMock()
        
        with patch("src.dependencies.UserService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_by_id.return_value = mock_user
            mock_service_class.return_value = mock_service
            
            with pytest.raises(AuthenticationError) as exc_info:
                await get_current_user(user_id, mock_db)
            
            assert "deactivated" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_returns_active_user(self):
        """Should return user when found and active."""
        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.is_active = True
        mock_db = AsyncMock()
        
        with patch("src.dependencies.UserService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_by_id.return_value = mock_user
            mock_service_class.return_value = mock_service
            
            result = await get_current_user(user_id, mock_db)
            
            assert result == mock_user


class TestGetCurrentActiveUser:
    """Tests for get_current_active_user function."""

    @pytest.mark.asyncio
    async def test_returns_user(self):
        """Should return the current user."""
        mock_user = MagicMock()
        mock_user.is_active = True
        
        result = await get_current_active_user(mock_user)
        
        assert result == mock_user
