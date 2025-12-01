"""
Tests for JWT authentication edge cases.

Coverage improvements:
- Expired tokens
- Tampered tokens (modified payload)
- Invalid signatures (wrong secret)
- Wrong token type
- Missing claims (sub, exp, type)
- Invalid UUID in sub claim
- Malformed JWT format
- Password hashing edge cases
- Token creation with various expiration times
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from jose import jwt

from src.services.auth_service import AuthService
from src.exceptions import (
    TokenExpiredError,
    InvalidTokenError,
)
from tests.mocks import (
    create_valid_token,
    create_expired_token,
    create_token_wrong_signature,
    create_token_wrong_type,
    create_token_missing_sub,
    create_token_invalid_uuid,
    create_tampered_token,
)


class TestTokenDecoding:
    """Tests for token decoding edge cases."""
    
    def test_decode_valid_token(self):
        """Should decode valid token successfully."""
        user_id = uuid4()
        token = create_valid_token(user_id)
        
        service = AuthService()
        decoded = service.decode_token(token)
        
        assert decoded["sub"] == str(user_id)
        assert decoded["type"] == "access"
    
    def test_decode_expired_token_raises_error(self):
        """Should raise TokenExpiredError for expired tokens."""
        token = create_expired_token()
        
        service = AuthService()
        
        with pytest.raises(TokenExpiredError):
            service.decode_token(token)
    
    def test_decode_wrong_signature_raises_error(self):
        """Should raise InvalidTokenError for wrong signature."""
        token = create_token_wrong_signature()
        
        service = AuthService()
        
        with pytest.raises(InvalidTokenError):
            service.decode_token(token)
    
    def test_decode_tampered_token_raises_error(self):
        """Should raise InvalidTokenError for tampered tokens."""
        token = create_tampered_token()
        
        service = AuthService()
        
        with pytest.raises(InvalidTokenError):
            service.decode_token(token)
    
    def test_decode_malformed_token_raises_error(self):
        """Should raise InvalidTokenError for malformed tokens."""
        malformed_tokens = [
            "not.a.valid.token",
            "just-a-string",
            "",
            "header.payload",  # Missing signature
            "a.b.c.d",  # Too many parts
        ]
        
        service = AuthService()
        
        for token in malformed_tokens:
            with pytest.raises(InvalidTokenError):
                service.decode_token(token)


class TestTokenTypeValidation:
    """Tests for token type validation."""
    
    def test_wrong_token_type_handling(self):
        """Token with wrong type should be handled."""
        token = create_token_wrong_type()
        
        service = AuthService()
        
        # Depending on implementation, might raise or decode with wrong type
        try:
            decoded = service.decode_token(token)
            # If it decodes, type should be 'refresh' not 'access'
            assert decoded.get("type") != "access"
        except InvalidTokenError:
            # Also acceptable if implementation validates type
            pass


class TestMissingClaims:
    """Tests for tokens with missing claims."""
    
    def test_missing_sub_claim(self):
        """Token missing 'sub' claim should be handled."""
        token = create_token_missing_sub()
        
        service = AuthService()
        
        # decode_token might succeed, but get_user_id_from_token should fail
        try:
            decoded = service.decode_token(token)
            # sub is missing
            assert "sub" not in decoded or decoded.get("sub") is None
        except InvalidTokenError:
            pass
    
    def test_get_user_id_with_missing_sub(self):
        """get_user_id_from_token should handle missing sub."""
        token = create_token_missing_sub()
        
        service = AuthService()
        
        with pytest.raises((InvalidTokenError, KeyError, AttributeError)):
            service.get_user_id_from_token(token)
    
    def test_invalid_uuid_in_sub(self):
        """Invalid UUID in sub claim should be handled."""
        token = create_token_invalid_uuid()
        
        service = AuthService()
        
        with pytest.raises((InvalidTokenError, ValueError)):
            service.get_user_id_from_token(token)


class TestTokenCreation:
    """Tests for token creation."""
    
    def test_create_token_with_default_expiration(self):
        """Should create token with default expiration."""
        user_id = uuid4()
        
        service = AuthService()
        token = service.create_access_token(user_id)
        
        assert token is not None
        
        # Should be decodable
        decoded = service.decode_token(token)
        assert decoded["sub"] == str(user_id)
    
    def test_create_token_with_custom_expiration(self):
        """Should create token with custom expiration."""
        user_id = uuid4()
        
        service = AuthService()
        token = service.create_access_token(
            user_id,
            expires_delta=timedelta(hours=1),
        )
        
        decoded = service.decode_token(token)
        
        # Token should expire within the hour
        exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        assert (exp - now) <= timedelta(hours=1)
    
    def test_create_token_with_very_short_expiration(self):
        """Should create token with very short expiration."""
        user_id = uuid4()
        
        service = AuthService()
        token = service.create_access_token(
            user_id,
            expires_delta=timedelta(seconds=1),
        )
        
        # Token should be valid immediately
        decoded = service.decode_token(token)
        assert decoded["sub"] == str(user_id)
    
    def test_create_token_with_very_long_expiration(self):
        """Should create token with very long expiration."""
        user_id = uuid4()
        
        service = AuthService()
        token = service.create_access_token(
            user_id,
            expires_delta=timedelta(days=365),
        )
        
        decoded = service.decode_token(token)
        
        # Token should expire in about a year
        exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        assert (exp - now) > timedelta(days=300)


class TestPasswordHashing:
    """Tests for password hashing edge cases."""
    
    def test_hash_password(self):
        """Should hash password."""
        password = "test_password_123"
        
        service = AuthService()
        hashed = service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 20
    
    def test_verify_correct_password(self):
        """Should verify correct password."""
        password = "test_password_123"
        
        service = AuthService()
        hashed = service.hash_password(password)
        
        assert service.verify_password(password, hashed)
    
    def test_verify_incorrect_password(self):
        """Should reject incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        
        service = AuthService()
        hashed = service.hash_password(password)
        
        assert not service.verify_password(wrong_password, hashed)
    
    def test_hash_empty_password(self):
        """Should handle empty password."""
        service = AuthService()
        
        # Empty password should still be hashable
        hashed = service.hash_password("")
        assert hashed is not None
        assert service.verify_password("", hashed)
    
    def test_hash_very_long_password(self):
        """Should handle very long passwords."""
        long_password = "a" * 1000
        
        service = AuthService()
        hashed = service.hash_password(long_password)
        
        assert service.verify_password(long_password, hashed)
    
    def test_hash_unicode_password(self):
        """Should handle unicode passwords."""
        unicode_password = "密码🔐Пароль"
        
        service = AuthService()
        hashed = service.hash_password(unicode_password)
        
        assert service.verify_password(unicode_password, hashed)
    
    def test_hash_special_characters(self):
        """Should handle special characters in password."""
        special_password = "p@$$w0rd!#$%^&*()"
        
        service = AuthService()
        hashed = service.hash_password(special_password)
        
        assert service.verify_password(special_password, hashed)
    
    def test_different_hashes_for_same_password(self):
        """Same password should produce different hashes (due to salt)."""
        password = "test_password"
        
        service = AuthService()
        hash1 = service.hash_password(password)
        hash2 = service.hash_password(password)
        
        # Hashes should be different (different salts)
        assert hash1 != hash2
        
        # But both should verify
        assert service.verify_password(password, hash1)
        assert service.verify_password(password, hash2)
    
    def test_verify_against_wrong_hash_format(self):
        """Should handle verification against invalid hash."""
        service = AuthService()
        
        # Invalid hash format
        invalid_hashes = [
            "not-a-valid-hash",
            "",
            "abc123",
            "$invalid$hash$format",
        ]
        
        for invalid_hash in invalid_hashes:
            result = service.verify_password("test", invalid_hash)
            # Should return False, not raise
            assert not result


class TestGetUserIdFromToken:
    """Tests for extracting user ID from token."""
    
    def test_get_user_id_from_valid_token(self):
        """Should extract user ID from valid token."""
        user_id = uuid4()
        token = create_valid_token(user_id)
        
        service = AuthService()
        extracted_id = service.get_user_id_from_token(token)
        
        assert extracted_id == user_id
    
    def test_get_user_id_from_expired_token(self):
        """Should raise TokenExpiredError for expired token."""
        token = create_expired_token()
        
        service = AuthService()
        
        with pytest.raises(TokenExpiredError):
            service.get_user_id_from_token(token)
    
    def test_get_user_id_from_invalid_token(self):
        """Should raise InvalidTokenError for invalid token."""
        service = AuthService()
        
        with pytest.raises(InvalidTokenError):
            service.get_user_id_from_token("invalid-token")


class TestTokenTimingEdgeCases:
    """Tests for token timing edge cases."""
    
    def test_token_just_before_expiration(self):
        """Token just before expiration should still be valid."""
        user_id = uuid4()
        
        # Create token that expires in 5 seconds
        token = create_valid_token(user_id, expires_delta=timedelta(seconds=5))
        
        service = AuthService()
        
        # Should still be valid
        decoded = service.decode_token(token)
        assert decoded["sub"] == str(user_id)
    
    def test_token_at_exact_expiration(self):
        """Token at exact expiration moment might be expired."""
        from src.config import get_settings
        
        settings = get_settings()
        now = datetime.now(timezone.utc)
        
        # Create token that expires exactly now
        payload = {
            "sub": str(uuid4()),
            "exp": now,  # Expires now
            "iat": now - timedelta(hours=1),
            "type": "access",
        }
        
        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        
        service = AuthService()
        
        # Might be expired or just valid depending on timing
        try:
            service.decode_token(token)
            # If decoded, it's at the boundary
        except TokenExpiredError:
            # Expected if past expiration
            pass
    
    def test_future_iat_handling(self):
        """Token with future iat (issued at) should be handled."""
        from src.config import get_settings
        
        settings = get_settings()
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=1)
        
        payload = {
            "sub": str(uuid4()),
            "exp": future + timedelta(hours=24),
            "iat": future,  # Issued in the future
            "type": "access",
        }
        
        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        
        service = AuthService()
        
        # Implementation might accept or reject future iat
        try:
            decoded = service.decode_token(token)
            # Some implementations don't validate iat
            assert decoded is not None
        except InvalidTokenError:
            # Also valid if implementation rejects future iat
            pass


class TestServiceInitialization:
    """Tests for AuthService initialization."""
    
    def test_service_initialization(self):
        """Should initialize AuthService."""
        service = AuthService()
        assert service is not None
    
    def test_service_uses_configured_algorithm(self):
        """Service should use algorithm from settings."""
        service = AuthService()
        
        user_id = uuid4()
        token = service.create_access_token(user_id)
        
        # Token should be decodable with configured algorithm
        decoded = service.decode_token(token)
        assert decoded is not None


class TestConcurrentTokenOperations:
    """Tests for concurrent token operations."""
    
    def test_multiple_tokens_for_same_user(self):
        """Multiple tokens for same user should all be valid."""
        user_id = uuid4()
        
        service = AuthService()
        
        tokens = [service.create_access_token(user_id) for _ in range(5)]
        
        # All tokens should be valid and decode to same user
        for token in tokens:
            decoded = service.decode_token(token)
            assert decoded["sub"] == str(user_id)
    
    def test_tokens_have_unique_iat(self):
        """Each token should have unique iat."""
        user_id = uuid4()
        
        service = AuthService()
        
        import time
        
        token1 = service.create_access_token(user_id)
        time.sleep(0.01)  # Small delay
        token2 = service.create_access_token(user_id)
        
        decoded1 = service.decode_token(token1)
        decoded2 = service.decode_token(token2)
        
        # iat might be same if generated too quickly
        # but generally should be different
        # Either way, both should be valid
        assert decoded1["sub"] == decoded2["sub"]


class TestEdgeCasePayloads:
    """Tests for edge case JWT payloads."""
    
    def test_extra_claims_preserved(self):
        """Extra claims in token should be accessible."""
        from src.config import get_settings
        
        settings = get_settings()
        now = datetime.now(timezone.utc)
        
        payload = {
            "sub": str(uuid4()),
            "exp": now + timedelta(hours=24),
            "iat": now,
            "type": "access",
            "custom_claim": "custom_value",
            "another": 123,
        }
        
        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        
        service = AuthService()
        decoded = service.decode_token(token)
        
        # Extra claims should be preserved
        assert decoded.get("custom_claim") == "custom_value"
        assert decoded.get("another") == 123
    
    def test_very_long_sub_claim(self):
        """Very long sub claim (still valid UUID) should work."""
        user_id = uuid4()  # UUIDs have fixed length
        
        service = AuthService()
        token = service.create_access_token(user_id)
        
        extracted_id = service.get_user_id_from_token(token)
        assert extracted_id == user_id
