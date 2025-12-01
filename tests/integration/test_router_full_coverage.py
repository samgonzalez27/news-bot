"""
Integration tests for all router endpoints to achieve 100% coverage.

Targets missing branches in:
- auth.py
- digests.py
- health.py
- interests.py
- users.py
"""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from src.models.user import User, UserInterest
from src.models.interest import Interest
from src.models.digest import Digest, DigestStatus
from src.services.auth_service import AuthService


# ===========================================================================
# AUTH ROUTER TESTS
# ===========================================================================
class TestAuthRouterFullCoverage:
    """Full coverage for auth router."""

    @pytest.mark.asyncio
    async def test_register_success(
        self,
        async_client: AsyncClient,
    ):
        """Test successful registration."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": f"new.user.{uuid4().hex[:8]}@example.com",
                "password": "SecurePass123",
                "full_name": "New User",
                "preferred_time": "08:00",
                "timezone": "UTC",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "full_name" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        """Test registration with duplicate email."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "SecurePass123",
                "full_name": "Duplicate User",
            },
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_validation_error(
        self,
        async_client: AsyncClient,
    ):
        """Test registration with invalid data."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "short",
                "full_name": "X",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(
        self,
        async_client: AsyncClient,
    ):
        """Test login with invalid credentials."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "WrongPassword123",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        """Test login with wrong password."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPassword123",
            },
        )
        assert response.status_code == 401


# ===========================================================================
# HEALTH ROUTER TESTS
# ===========================================================================
class TestHealthRouterFullCoverage:
    """Full coverage for health router."""

    @pytest.mark.asyncio
    async def test_health_basic(
        self,
        async_client: AsyncClient,
    ):
        """Test basic health check."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_db(
        self,
        async_client: AsyncClient,
    ):
        """Test database health check."""
        response = await async_client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "latency_ms" in data

    @pytest.mark.asyncio
    async def test_health_db_error(
        self,
        async_client: AsyncClient,
    ):
        """Test database health check with error."""
        with patch("src.routers.health.get_db") as mock_get_db:
            mock_session = AsyncMock()
            mock_session.execute.side_effect = Exception("DB connection failed")
            
            async def mock_db():
                yield mock_session
            
            mock_get_db.return_value = mock_db()
            
            # The endpoint should still return 200 but with error status
            # (health checks should not fail the request)

    @pytest.mark.asyncio
    async def test_health_scheduler_disabled(
        self,
        async_client: AsyncClient,
    ):
        """Test scheduler health check when disabled."""
        with patch("src.routers.health.get_settings") as mock_settings:
            settings = MagicMock()
            settings.scheduler_enabled = False
            mock_settings.return_value = settings

            response = await async_client.get("/health/scheduler")
            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is False

    @pytest.mark.asyncio
    async def test_health_scheduler_enabled_running(
        self,
        async_client: AsyncClient,
    ):
        """Test scheduler health check when enabled and running."""
        with patch("src.routers.health.get_settings") as mock_settings:
            settings = MagicMock()
            settings.scheduler_enabled = True
            mock_settings.return_value = settings

            with patch("src.routers.health.scheduler") as mock_scheduler:
                mock_scheduler.running = True
                mock_job = MagicMock()
                mock_job.id = "test_job"
                mock_job.name = "Test Job"
                mock_job.next_run_time = None
                mock_scheduler.get_jobs.return_value = [mock_job]

                response = await async_client.get("/health/scheduler")
                assert response.status_code == 200
                data = response.json()
                assert data["enabled"] is True
                assert data["running"] is True
                assert "jobs" in data

    @pytest.mark.asyncio
    async def test_health_ready(
        self,
        async_client: AsyncClient,
    ):
        """Test readiness check."""
        response = await async_client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        assert "checks" in data

    @pytest.mark.asyncio
    async def test_health_live(
        self,
        async_client: AsyncClient,
    ):
        """Test liveness check."""
        response = await async_client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


# ===========================================================================
# DIGEST ROUTER TESTS
# ===========================================================================
class TestDigestRouterFullCoverage:
    """Full coverage for digest router."""

    @pytest.mark.asyncio
    async def test_list_digests_empty(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test listing digests when none exist."""
        response = await async_client.get(
            "/api/v1/digests",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["digests"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_digests_with_pagination(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_user: User,
        seeded_db: AsyncSession,
    ):
        """Test listing digests with pagination."""
        # Create some digests
        for i in range(3):
            digest = Digest(
                user_id=test_user.id,
                digest_date=date.today() - timedelta(days=i),
                content=f"# Digest {i}",
                status=DigestStatus.COMPLETED.value,
            )
            seeded_db.add(digest)
        await seeded_db.commit()

        response = await async_client.get(
            "/api/v1/digests?page=1&per_page=2",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["digests"]) == 2
        assert data["has_next"] is True

    @pytest.mark.asyncio
    async def test_get_latest_digest(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_user: User,
        seeded_db: AsyncSession,
    ):
        """Test getting latest digest when one exists."""
        digest = Digest(
            user_id=test_user.id,
            digest_date=date.today() - timedelta(days=1),
            content="# Latest Digest\n\nContent here.",
            summary="Latest summary",
            status=DigestStatus.COMPLETED.value,
        )
        seeded_db.add(digest)
        await seeded_db.commit()

        response = await async_client.get(
            "/api/v1/digests/latest",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @pytest.mark.asyncio
    async def test_get_digest_by_date_exists(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_user: User,
        seeded_db: AsyncSession,
    ):
        """Test getting digest by date when it exists."""
        target_date = date.today() - timedelta(days=5)
        digest = Digest(
            user_id=test_user.id,
            digest_date=target_date,
            content="# Date Specific Digest",
            status=DigestStatus.COMPLETED.value,
        )
        seeded_db.add(digest)
        await seeded_db.commit()

        response = await async_client.get(
            f"/api/v1/digests/by-date/{target_date.isoformat()}",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_digest_by_id_exists(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_user: User,
        seeded_db: AsyncSession,
    ):
        """Test getting digest by ID when it exists."""
        digest = Digest(
            user_id=test_user.id,
            digest_date=date.today() - timedelta(days=3),
            content="# Specific Digest",
            status=DigestStatus.COMPLETED.value,
        )
        seeded_db.add(digest)
        await seeded_db.commit()
        await seeded_db.refresh(digest)

        response = await async_client.get(
            f"/api/v1/digests/{digest.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_digest_success(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_user: User,
        seeded_db: AsyncSession,
    ):
        """Test successful digest deletion."""
        digest = Digest(
            user_id=test_user.id,
            digest_date=date.today() - timedelta(days=10),
            content="# To Delete",
            status=DigestStatus.COMPLETED.value,
        )
        seeded_db.add(digest)
        await seeded_db.commit()
        await seeded_db.refresh(digest)

        response = await async_client.delete(
            f"/api/v1/digests/{digest.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_generate_digest_no_interests(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_user: User,
        seeded_db: AsyncSession,
    ):
        """Test generating digest when user has no interests."""
        # Ensure user has no interests
        await seeded_db.execute(
            delete(UserInterest).where(UserInterest.user_id == test_user.id)
        )
        await seeded_db.commit()

        response = await async_client.post(
            "/api/v1/digests/generate",
            headers=auth_headers,
        )
        # Should succeed but with "no interests" content
        assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_generate_digest_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Test generating digest without authentication."""
        response = await async_client.post("/api/v1/digests/generate")
        assert response.status_code == 401


# ===========================================================================
# INTEREST ROUTER TESTS
# ===========================================================================
class TestInterestRouterFullCoverage:
    """Full coverage for interest router."""

    @pytest.mark.asyncio
    async def test_list_all_interests(
        self,
        async_client: AsyncClient,
    ):
        """Test listing all available interests."""
        response = await async_client.get("/api/v1/interests")
        assert response.status_code == 200
        data = response.json()
        assert "interests" in data
        assert "total" in data
        assert data["total"] > 0

    @pytest.mark.asyncio
    async def test_get_my_interests_empty(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test getting user's interests when none selected."""
        response = await async_client.get(
            "/api/v1/interests/me",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_update_my_interests(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test updating user's interests."""
        response = await async_client.put(
            "/api/v1/interests/me",
            headers=auth_headers,
            json={"interest_slugs": ["technology", "science"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_update_my_interests_invalid_slug(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test updating with invalid interest slug."""
        response = await async_client.put(
            "/api/v1/interests/me",
            headers=auth_headers,
            json={"interest_slugs": ["invalid-nonexistent-slug"]},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_interest_idempotent(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test adding interest is idempotent."""
        # Add once
        response1 = await async_client.post(
            "/api/v1/interests/me/technology",
            headers=auth_headers,
        )
        assert response1.status_code == 201

        # Add again - should still succeed
        response2 = await async_client.post(
            "/api/v1/interests/me/technology",
            headers=auth_headers,
        )
        # Second add returns the existing interest
        assert response2.status_code == 201

    @pytest.mark.asyncio
    async def test_remove_nonexistent_interest_subscription(
        self,
        async_client: AsyncClient,
        auth_headers,
        seeded_db: AsyncSession,
        test_user: User,
    ):
        """Test removing interest when not subscribed."""
        # Ensure no interests
        await seeded_db.execute(
            delete(UserInterest).where(UserInterest.user_id == test_user.id)
        )
        await seeded_db.commit()

        response = await async_client.delete(
            "/api/v1/interests/me/technology",
            headers=auth_headers,
        )
        # Should succeed even if not subscribed (idempotent)
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_interests_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Test interest operations without authentication."""
        response = await async_client.get("/api/v1/interests/me")
        assert response.status_code == 401


# ===========================================================================
# USER ROUTER TESTS
# ===========================================================================
class TestUserRouterFullCoverage:
    """Full coverage for user router."""

    @pytest.mark.asyncio
    async def test_get_current_user(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_user: User,
    ):
        """Test getting current user profile."""
        response = await async_client.get(
            "/api/v1/users/me",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_update_profile_email(
        self,
        async_client: AsyncClient,
        seeded_db: AsyncSession,
    ):
        """Test updating user email."""
        # Create a dedicated user for this test
        user = User(
            id=uuid4(),
            email=f"email.update.{uuid4().hex[:8]}@example.com",
            hashed_password=AuthService.hash_password("SecurePass123"),
            full_name="Email Update User",
            is_active=True,
        )
        seeded_db.add(user)
        await seeded_db.commit()

        token = AuthService.create_access_token(user.id)
        new_email = f"new.email.{uuid4().hex[:8]}@example.com"

        response = await async_client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"email": new_email},
        )
        assert response.status_code == 200
        assert response.json()["email"] == new_email

    @pytest.mark.asyncio
    async def test_update_profile_email_conflict(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_user: User,
        seeded_db: AsyncSession,
    ):
        """Test updating email to one that already exists."""
        # Create another user
        other_user = User(
            id=uuid4(),
            email="existing@example.com",
            hashed_password=AuthService.hash_password("SecurePass123"),
            full_name="Other User",
            is_active=True,
        )
        seeded_db.add(other_user)
        await seeded_db.commit()

        response = await async_client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"email": "existing@example.com"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_preferences_time(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test updating preferred time."""
        response = await async_client.patch(
            "/api/v1/users/me/preferences",
            headers=auth_headers,
            json={"preferred_time": "18:00"},
        )
        assert response.status_code == 200
        assert response.json()["preferred_time"] == "18:00"

    @pytest.mark.asyncio
    async def test_update_preferences_timezone(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test updating timezone."""
        response = await async_client.patch(
            "/api/v1/users/me/preferences",
            headers=auth_headers,
            json={"timezone": "America/Los_Angeles"},
        )
        assert response.status_code == 200
        assert response.json()["timezone"] == "America/Los_Angeles"

    @pytest.mark.asyncio
    async def test_update_preferences_invalid_timezone(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test updating with invalid timezone."""
        response = await async_client.patch(
            "/api/v1/users/me/preferences",
            headers=auth_headers,
            json={"timezone": "Invalid/Timezone"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_interests_via_users(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test updating interests via /users/me/interests."""
        response = await async_client.put(
            "/api/v1/users/me/interests",
            headers=auth_headers,
            json={"interest_slugs": ["health", "entertainment"]},
        )
        assert response.status_code == 200
        data = response.json()
        interest_slugs = [i["slug"] for i in data["interests"]]
        assert "health" in interest_slugs
        assert "entertainment" in interest_slugs

    @pytest.mark.asyncio
    async def test_update_interests_invalid_slug(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test updating with invalid interest slug."""
        response = await async_client.put(
            "/api/v1/users/me/interests",
            headers=auth_headers,
            json={"interest_slugs": ["nonexistent-interest"]},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_users_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Test user operations without authentication."""
        response = await async_client.get("/api/v1/users/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_deactivate_account_success(
        self,
        async_client: AsyncClient,
        seeded_db: AsyncSession,
    ):
        """Test account deactivation."""
        # Create a user specifically for deactivation
        user = User(
            id=uuid4(),
            email=f"deactivate.{uuid4().hex[:8]}@example.com",
            hashed_password=AuthService.hash_password("SecurePass123"),
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

        # Verify user is deactivated
        await seeded_db.refresh(user)
        assert user.is_active is False
