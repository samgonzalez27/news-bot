"""
Unit tests for the authentication service.
"""

from datetime import timedelta
from uuid import uuid4

import pytest

from src.services.auth_service import AuthService
from src.exceptions import InvalidTokenError, TokenExpiredError


class TestPasswordHashing:
    """Tests for password hashing functionality."""

    def test_hash_password_returns_hash(self):
        """Password hashing should return a hash string."""
        password = "TestPassword123"
        hashed = AuthService.hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_different_for_same_input(self):
        """Same password should produce different hashes (due to salt)."""
        password = "TestPassword123"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        password = "TestPassword123"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Incorrect password should fail verification."""
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(wrong_password, hashed) is False

    def test_verify_password_invalid_hash(self):
        """Invalid hash format should return False."""
        result = AuthService.verify_password("password", "invalid-hash")
        assert result is False


class TestJWTTokens:
    """Tests for JWT token functionality."""

    def test_create_access_token(self):
        """Access token creation should return a valid token string."""
        user_id = uuid4()
        token = AuthService.create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Valid token should decode successfully."""
        user_id = uuid4()
        token = AuthService.create_access_token(user_id)
        payload = AuthService.decode_token(token)

        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_invalid_token(self):
        """Invalid token should raise InvalidTokenError."""
        with pytest.raises(InvalidTokenError):
            AuthService.decode_token("invalid-token")

    def test_decode_expired_token(self):
        """Expired token should raise TokenExpiredError."""
        user_id = uuid4()
        # Create token that expires immediately
        token = AuthService.create_access_token(
            user_id,
            expires_delta=timedelta(seconds=-1),
        )

        with pytest.raises(TokenExpiredError):
            AuthService.decode_token(token)

    def test_get_user_id_from_token(self):
        """Should extract user ID from valid token."""
        user_id = uuid4()
        token = AuthService.create_access_token(user_id)
        extracted_id = AuthService.get_user_id_from_token(token)

        assert extracted_id == user_id

    def test_get_user_id_from_invalid_token(self):
        """Should raise InvalidTokenError for invalid token."""
        with pytest.raises(InvalidTokenError):
            AuthService.get_user_id_from_token("invalid-token")

    def test_get_token_expiry_seconds(self):
        """Should return correct expiry time in seconds."""
        expiry = AuthService.get_token_expiry_seconds()
        assert expiry > 0
        assert isinstance(expiry, int)

    def test_custom_expiration(self):
        """Token with custom expiration should be valid."""
        user_id = uuid4()
        token = AuthService.create_access_token(
            user_id,
            expires_delta=timedelta(hours=2),
        )
        payload = AuthService.decode_token(token)

        assert payload["sub"] == str(user_id)
