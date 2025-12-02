"""
User service for user account management.
"""

from datetime import time
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.exceptions import DuplicateError, NotFoundError
from src.logging_config import get_logger
from src.models.user import User
from src.schemas.user import UserCreate, UserPreferencesUpdate, UserUpdate
from src.services.auth_service import AuthService

logger = get_logger("user_service")


class UserService:
    """Service for user CRUD operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize user service.

        Args:
            db: Database session.
        """
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user account.

        Args:
            user_data: User registration data.

        Returns:
            User: Created user object.

        Raises:
            DuplicateError: If email already exists.
        """
        # Check for existing email
        existing = await self.get_by_email(user_data.email)
        if existing:
            logger.warning(f"Duplicate email registration attempt: {user_data.email}")
            raise DuplicateError("User", "email")

        # Parse preferred time
        preferred_time = time.fromisoformat(user_data.preferred_time)

        # Create user
        user = User(
            email=user_data.email.lower(),
            hashed_password=AuthService.hash_password(user_data.password),
            full_name=user_data.full_name,
            preferred_time=preferred_time,
            # NOTE: Timezone support disabled - all users use UTC
            # timezone=user_data.timezone,
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        logger.info(f"Created user: {user.id} ({user.email})")
        return user

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get a user by their ID.

        Args:
            user_id: User's unique identifier.

        Returns:
            Optional[User]: User if found, None otherwise.
        """
        stmt = (
            select(User)
            .options(selectinload(User.interests))
            .where(User.id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by their email address.

        Args:
            email: User's email address.

        Returns:
            Optional[User]: User if found, None otherwise.
        """
        stmt = (
            select(User)
            .options(selectinload(User.interests))
            .where(User.email == email.lower())
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user(
        self,
        user_id: UUID,
        update_data: UserUpdate,
    ) -> User:
        """
        Update user profile information.

        Args:
            user_id: User's unique identifier.
            update_data: Fields to update.

        Returns:
            User: Updated user object.

        Raises:
            NotFoundError: If user not found.
            DuplicateError: If new email already exists.
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))

        # Check for email conflict
        if update_data.email and update_data.email.lower() != user.email:
            existing = await self.get_by_email(update_data.email)
            if existing:
                raise DuplicateError("User", "email")
            user.email = update_data.email.lower()

        # Update other fields
        if update_data.full_name is not None:
            user.full_name = update_data.full_name

        await self.db.flush()
        await self.db.refresh(user)

        logger.info(f"Updated user profile: {user.id}")
        return user

    async def update_preferences(
        self,
        user_id: UUID,
        preferences: UserPreferencesUpdate,
    ) -> User:
        """
        Update user digest preferences.

        Args:
            user_id: User's unique identifier.
            preferences: Preference fields to update.

        Returns:
            User: Updated user object.

        Raises:
            NotFoundError: If user not found.
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))

        if preferences.preferred_time is not None:
            user.preferred_time = time.fromisoformat(preferences.preferred_time)

        # NOTE: Timezone support disabled - all users use UTC
        # if preferences.timezone is not None:
        #     user.timezone = preferences.timezone

        await self.db.flush()
        await self.db.refresh(user)

        logger.info(f"Updated user preferences: {user.id}")
        return user

    async def deactivate_user(self, user_id: UUID) -> User:
        """
        Deactivate a user account.

        Args:
            user_id: User's unique identifier.

        Returns:
            User: Deactivated user object.

        Raises:
            NotFoundError: If user not found.
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))

        user.is_active = False
        await self.db.flush()

        logger.info(f"Deactivated user: {user.id}")
        return user

    async def verify_credentials(
        self,
        email: str,
        password: str,
    ) -> Optional[User]:
        """
        Verify user login credentials.

        Args:
            email: User's email address.
            password: Plain text password.

        Returns:
            Optional[User]: User if credentials valid, None otherwise.
        """
        user = await self.get_by_email(email)
        if not user:
            logger.debug(f"Login attempt for non-existent email: {email}")
            return None

        if not user.is_active:
            logger.debug(f"Login attempt for inactive user: {email}")
            return None

        if not AuthService.verify_password(password, user.hashed_password):
            logger.debug(f"Invalid password for user: {email}")
            return None

        logger.info(f"Successful login: {user.id} ({user.email})")
        return user
