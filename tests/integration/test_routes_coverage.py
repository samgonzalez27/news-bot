"""
Additional route tests to increase coverage.

Tests routes that were missing coverage in the original test suite.
"""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.services.auth_service import AuthService


class TestAuthRouterCoverage:
    """Test auth router uncovered paths."""

    @pytest.mark.asyncio
    async def test_login_success_returns_token(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        """Test successful login returns valid token response."""
        # test_user is already created with password "TestPassword123"
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["expires_in"] > 0

    @pytest.mark.asyncio
    async def test_login_generates_valid_jwt(
        self,
        async_client: AsyncClient,
        seeded_db: AsyncSession,
    ):
        """Test that login generates a token that can be used for auth."""
        # Create a user directly
        user = User(
            id=uuid4(),
            email="jwttest@example.com",
            hashed_password=AuthService.hash_password("SecurePass456"),
            full_name="JWT Test User",
            is_active=True,
        )
        seeded_db.add(user)
        await seeded_db.commit()

        # Login
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "jwttest@example.com", "password": "SecurePass456"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Use the token
        profile_response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile_response.status_code == 200
        assert profile_response.json()["email"] == "jwttest@example.com"


class TestDigestRouterCoverage:
    """Test digest router uncovered paths."""

    @pytest.mark.asyncio
    async def test_get_latest_digest_not_found(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test getting latest digest when none exists."""
        response = await async_client.get(
            "/api/v1/digests/latest",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_digest_by_date_not_found(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test getting digest by date when none exists."""
        response = await async_client.get(
            "/api/v1/digests/by-date/2024-01-01",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_digest_by_id_not_found(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test getting digest by ID when not found."""
        fake_id = str(uuid4())
        response = await async_client.get(
            f"/api/v1/digests/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_digest_not_found(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test deleting a digest that doesn't exist."""
        fake_id = str(uuid4())
        response = await async_client.delete(
            f"/api/v1/digests/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_digest_success(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_user: User,
        seeded_db: AsyncSession,
    ):
        """Test successful digest generation."""
        from src.models.interest import Interest
        from src.models.user import UserInterest
        from sqlalchemy import select

        # Add interest to user
        interest_stmt = select(Interest).limit(1)
        result = await seeded_db.execute(interest_stmt)
        interest = result.scalar_one_or_none()
        
        if interest:
            user_interest = UserInterest(
                user_id=test_user.id,
                interest_id=interest.id,
            )
            seeded_db.add(user_interest)
            await seeded_db.commit()

        # Mock the external services
        with patch("src.services.digest_service.get_news_service") as mock_news, \
             patch("src.services.digest_service.get_openai_service") as mock_openai:
            
            mock_news_instance = AsyncMock()
            mock_news_instance.get_previous_day_headlines = AsyncMock(return_value=[
                {"title": "Test Headline", "source": "Test Source"}
            ])
            mock_news.return_value = mock_news_instance
            
            mock_openai_instance = AsyncMock()
            mock_openai_instance.generate_digest = AsyncMock(return_value={
                "content": "# Test Digest\n\nTest content.",
                "summary": "Test summary",
                "word_count": 5,
            })
            mock_openai.return_value = mock_openai_instance

            response = await async_client.post(
                "/api/v1/digests/generate",
                headers=auth_headers,
            )
            
            # May return 201 or 200 depending on whether digest already exists
            assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_regenerate_digest(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_user: User,
        seeded_db: AsyncSession,
    ):
        """Test digest regeneration with force flag."""
        from src.models.interest import Interest
        from src.models.user import UserInterest
        from sqlalchemy import select, delete

        # Add interest to user
        interest_stmt = select(Interest).limit(1)
        result = await seeded_db.execute(interest_stmt)
        interest = result.scalar_one_or_none()
        
        if interest:
            # Clear existing interests first
            await seeded_db.execute(
                delete(UserInterest).where(UserInterest.user_id == test_user.id)
            )
            user_interest = UserInterest(
                user_id=test_user.id,
                interest_id=interest.id,
            )
            seeded_db.add(user_interest)
            await seeded_db.commit()

        yesterday = (date.today() - timedelta(days=1)).isoformat()

        with patch("src.services.digest_service.get_news_service") as mock_news, \
             patch("src.services.digest_service.get_openai_service") as mock_openai:
            
            mock_news_instance = AsyncMock()
            mock_news_instance.get_previous_day_headlines = AsyncMock(return_value=[
                {"title": "Test Headline", "source": "Test Source"}
            ])
            mock_news.return_value = mock_news_instance
            
            mock_openai_instance = AsyncMock()
            mock_openai_instance.generate_digest = AsyncMock(return_value={
                "content": "# Regenerated Digest\n\nNew content.",
                "summary": "Regenerated summary",
                "word_count": 6,
            })
            mock_openai.return_value = mock_openai_instance

            response = await async_client.post(
                f"/api/v1/digests/regenerate/{yesterday}",
                headers=auth_headers,
            )
            
            assert response.status_code == 200


class TestUserRouterCoverage:
    """Test user router uncovered paths."""

    @pytest.mark.asyncio
    async def test_update_profile(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test updating user profile."""
        response = await async_client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"full_name": "Updated Name"},
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_preferences(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test updating user preferences."""
        response = await async_client.patch(
            "/api/v1/users/me/preferences",
            headers=auth_headers,
            json={"preferred_time": "09:00"},
            # NOTE: timezone field disabled - all users use UTC
            # json={"preferred_time": "09:00", "timezone": "America/New_York"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["preferred_time"] == "09:00"
        # assert data["timezone"] == "America/New_York"  # timezone disabled

    @pytest.mark.asyncio
    async def test_deactivate_account(
        self,
        async_client: AsyncClient,
        seeded_db: AsyncSession,
    ):
        """Test account deactivation."""
        # Create a user specifically for deactivation
        user = User(
            id=uuid4(),
            email="deactivate@example.com",
            hashed_password=AuthService.hash_password("Deactivate123"),
            full_name="Deactivate User",
            is_active=True,
        )
        seeded_db.add(user)
        await seeded_db.commit()
        
        token = AuthService.create_access_token(user.id)
        
        response = await async_client.delete(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204


class TestInterestRouterCoverage:
    """Test interest router uncovered paths."""

    @pytest.mark.asyncio
    async def test_add_single_interest(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test adding a single interest."""
        response = await async_client.post(
            "/api/v1/interests/me/technology",
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["slug"] == "technology"

    @pytest.mark.asyncio
    async def test_add_interest_not_found(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test adding non-existent interest."""
        response = await async_client.post(
            "/api/v1/interests/me/nonexistent-interest-xyz",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_remove_single_interest(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test removing a single interest."""
        # First add an interest
        await async_client.post(
            "/api/v1/interests/me/technology",
            headers=auth_headers,
        )

        # Then remove it
        response = await async_client.delete(
            "/api/v1/interests/me/technology",
            headers=auth_headers,
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_remove_interest_not_found(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test removing non-existent interest."""
        response = await async_client.delete(
            "/api/v1/interests/me/nonexistent-interest-xyz",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDigestServiceCoverage:
    """Test digest service uncovered paths."""

    @pytest.mark.asyncio
    async def test_create_empty_digest_no_interests(
        self,
        seeded_db: AsyncSession,
        test_user: User,
    ):
        """Test creating digest when user has no interests."""
        from src.services.digest_service import DigestService
        from src.models.user import UserInterest
        from sqlalchemy import delete
        
        # Ensure user has no interests
        await seeded_db.execute(
            delete(UserInterest).where(UserInterest.user_id == test_user.id)
        )
        await seeded_db.commit()

        service = DigestService(seeded_db)
        
        with patch("src.services.digest_service.get_news_service"), \
             patch("src.services.digest_service.get_openai_service"):
            digest = await service.generate_digest(test_user.id)
        
        assert digest is not None
        assert "No interests selected" in digest.content

    @pytest.mark.asyncio
    async def test_generate_digest_returns_existing(
        self,
        seeded_db: AsyncSession,
        test_user: User,
    ):
        """Test that generating digest returns existing one if completed."""
        from src.services.digest_service import DigestService
        from src.models.digest import Digest, DigestStatus
        from datetime import date, timedelta

        yesterday = date.today() - timedelta(days=1)
        
        # Create an existing completed digest
        existing_digest = Digest(
            user_id=test_user.id,
            digest_date=yesterday,
            content="# Existing Digest\n\nExisting content.",
            summary="Existing summary",
            status=DigestStatus.COMPLETED.value,
            word_count=5,
        )
        seeded_db.add(existing_digest)
        await seeded_db.commit()
        await seeded_db.refresh(existing_digest)

        service = DigestService(seeded_db)
        
        # Should return the existing digest without regenerating
        result = await service.generate_digest(test_user.id, digest_date=yesterday)
        
        assert result.id == existing_digest.id
        assert result.content == "# Existing Digest\n\nExisting content."

    @pytest.mark.asyncio
    async def test_generate_digest_force_regenerate(
        self,
        seeded_db: AsyncSession,
        test_user: User,
    ):
        """Test that force=True regenerates existing digest."""
        from src.services.digest_service import DigestService
        from src.models.digest import Digest, DigestStatus
        from src.models.interest import Interest
        from src.models.user import UserInterest
        from sqlalchemy import select, delete
        from datetime import date, timedelta

        yesterday = date.today() - timedelta(days=1)

        # Ensure user has an interest
        interest_stmt = select(Interest).limit(1)
        result = await seeded_db.execute(interest_stmt)
        interest = result.scalar_one_or_none()
        
        if interest:
            # Clear and add interest
            await seeded_db.execute(
                delete(UserInterest).where(UserInterest.user_id == test_user.id)
            )
            user_interest = UserInterest(
                user_id=test_user.id,
                interest_id=interest.id,
            )
            seeded_db.add(user_interest)
            await seeded_db.commit()

        # Create existing digest
        existing_digest = Digest(
            user_id=test_user.id,
            digest_date=yesterday,
            content="# Old Digest\n\nOld content.",
            summary="Old summary",
            status=DigestStatus.COMPLETED.value,
            word_count=5,
        )
        seeded_db.add(existing_digest)
        await seeded_db.commit()

        service = DigestService(seeded_db)
        
        with patch("src.services.digest_service.get_news_service") as mock_news, \
             patch("src.services.digest_service.get_openai_service") as mock_openai:
            
            mock_news_instance = AsyncMock()
            mock_news_instance.get_previous_day_headlines = AsyncMock(return_value=[
                {"title": "New Headline", "source": "New Source"}
            ])
            mock_news.return_value = mock_news_instance
            
            mock_openai_instance = AsyncMock()
            mock_openai_instance.generate_digest = AsyncMock(return_value={
                "content": "# New Digest\n\nNew content.",
                "summary": "New summary",
                "word_count": 6,
            })
            mock_openai.return_value = mock_openai_instance

            # Force regeneration
            result = await service.generate_digest(
                test_user.id,
                digest_date=yesterday,
                force=True,
            )
        
        assert result.content == "# New Digest\n\nNew content."

    @pytest.mark.asyncio
    async def test_generate_digest_user_not_found(
        self,
        seeded_db: AsyncSession,
    ):
        """Test digest generation with non-existent user."""
        from src.services.digest_service import DigestService
        from src.exceptions import NotFoundError

        service = DigestService(seeded_db)
        
        fake_user_id = uuid4()
        
        with pytest.raises(NotFoundError):
            await service.generate_digest(fake_user_id)

    @pytest.mark.asyncio
    async def test_generate_digest_external_service_failure(
        self,
        seeded_db: AsyncSession,
        test_user: User,
    ):
        """Test digest generation when external service fails."""
        from src.services.digest_service import DigestService
        from src.models.interest import Interest
        from src.models.user import UserInterest
        from sqlalchemy import select, delete

        # Ensure user has an interest
        interest_stmt = select(Interest).limit(1)
        result = await seeded_db.execute(interest_stmt)
        interest = result.scalar_one_or_none()
        
        if interest:
            await seeded_db.execute(
                delete(UserInterest).where(UserInterest.user_id == test_user.id)
            )
            user_interest = UserInterest(
                user_id=test_user.id,
                interest_id=interest.id,
            )
            seeded_db.add(user_interest)
            await seeded_db.commit()

        service = DigestService(seeded_db)
        
        with patch("src.services.digest_service.get_news_service") as mock_news:
            mock_news_instance = AsyncMock()
            mock_news_instance.get_previous_day_headlines = AsyncMock(
                side_effect=Exception("News API unavailable")
            )
            mock_news.return_value = mock_news_instance

            with pytest.raises(Exception, match="News API unavailable"):
                await service.generate_digest(test_user.id)


class TestMainAppCoverage:
    """Test main app uncovered paths."""

    @pytest.mark.asyncio
    async def test_health_endpoint(
        self,
        async_client: AsyncClient,
    ):
        """Test health check endpoint."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(
        self,
        async_client: AsyncClient,
    ):
        """Test root endpoint."""
        response = await async_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["docs"] == "/docs"
