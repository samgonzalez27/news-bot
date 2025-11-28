"""
Authentication service for password hashing and JWT token management.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import argon2
from jose import JWTError, jwt

from src.config import get_settings
from src.exceptions import InvalidTokenError, TokenExpiredError
from src.logging_config import get_logger

logger = get_logger("auth_service")

# Argon2 password hasher with secure defaults
password_hasher = argon2.PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
)


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using Argon2id.

        Args:
            password: Plain text password.

        Returns:
            str: Argon2id hashed password.
        """
        return password_hasher.hash(password)

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: Plain text password to verify.
            hashed_password: Stored Argon2id hash.

        Returns:
            bool: True if password matches, False otherwise.
        """
        try:
            password_hasher.verify(hashed_password, password)
            return True
        except argon2.exceptions.VerifyMismatchError:
            return False
        except argon2.exceptions.InvalidHashError:
            logger.error("Invalid password hash format encountered")
            return False

    @staticmethod
    def create_access_token(
        user_id: UUID,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: User's unique identifier.
            expires_delta: Optional custom expiration time.

        Returns:
            str: Encoded JWT token.
        """
        settings = get_settings()
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)

        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": now,
            "type": "access",
        }

        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        logger.debug(f"Created access token for user {user_id}")
        return token

    @staticmethod
    def decode_token(token: str) -> dict:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token string.

        Returns:
            dict: Decoded token payload.

        Raises:
            TokenExpiredError: If token has expired.
            InvalidTokenError: If token is invalid.
        """
        settings = get_settings()
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )

            # Verify token type
            if payload.get("type") != "access":
                raise InvalidTokenError("Invalid token type")

            return payload

        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            raise TokenExpiredError()
        except JWTError as e:
            logger.debug(f"Token validation failed: {e}")
            raise InvalidTokenError()

    @staticmethod
    def get_user_id_from_token(token: str) -> UUID:
        """
        Extract user ID from a JWT token.

        Args:
            token: JWT token string.

        Returns:
            UUID: User's unique identifier.

        Raises:
            TokenExpiredError: If token has expired.
            InvalidTokenError: If token is invalid.
        """
        payload = AuthService.decode_token(token)
        user_id_str = payload.get("sub")

        if not user_id_str:
            raise InvalidTokenError("Token missing user ID")

        try:
            return UUID(user_id_str)
        except ValueError:
            raise InvalidTokenError("Invalid user ID in token")

    @staticmethod
    def get_token_expiry_seconds() -> int:
        """
        Get the token expiration time in seconds.

        Returns:
            int: Token expiration in seconds.
        """
        settings = get_settings()
        return settings.jwt_access_token_expire_minutes * 60
