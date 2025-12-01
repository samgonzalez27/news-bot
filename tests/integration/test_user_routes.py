"""
Integration tests for user routes.
"""

from fastapi import status


class TestGetCurrentUser:
    """Tests for GET /api/v1/users/me."""

    def test_get_current_user_success(self, client):
        """Should return current user profile."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "profile@example.com",
                "password": "SecurePass123",
                "full_name": "Profile User",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "profile@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        # Get profile
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "profile@example.com"
        assert data["full_name"] == "Profile User"
        assert "interests" in data

    def test_get_current_user_no_token(self, client):
        """Should reject request without token."""
        response = client.get("/api/v1/users/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_invalid_token(self, client):
        """Should reject request with invalid token."""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateCurrentUser:
    """Tests for PATCH /api/v1/users/me."""

    def test_update_full_name(self, client):
        """Should update user's full name."""
        # Setup
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "update@example.com",
                "password": "SecurePass123",
                "full_name": "Original Name",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "update@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        # Update
        response = client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Updated Name"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["full_name"] == "Updated Name"

    def test_update_email(self, client):
        """Should update user's email."""
        # Setup
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "oldemail@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "oldemail@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        # Update
        response = client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"email": "newemail@example.com"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == "newemail@example.com"

    def test_update_email_duplicate(self, client):
        """Should reject duplicate email."""
        # Create first user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "first@example.com",
                "password": "SecurePass123",
                "full_name": "First User",
            },
        )
        
        # Create second user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "second@example.com",
                "password": "SecurePass123",
                "full_name": "Second User",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "second@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        # Try to update to first user's email
        response = client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"email": "first@example.com"},
        )

        assert response.status_code == status.HTTP_409_CONFLICT


class TestUpdatePreferences:
    """Tests for PATCH /api/v1/users/me/preferences."""

    def test_update_preferred_time(self, client):
        """Should update preferred digest time."""
        # Setup
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "prefs@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
                "preferred_time": "08:00",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "prefs@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        # Update
        response = client.patch(
            "/api/v1/users/me/preferences",
            headers={"Authorization": f"Bearer {token}"},
            json={"preferred_time": "18:30"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["preferred_time"] == "18:30"

    def test_update_timezone(self, client):
        """Should update timezone."""
        # Setup
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "timezone@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "timezone@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        # Update
        response = client.patch(
            "/api/v1/users/me/preferences",
            headers={"Authorization": f"Bearer {token}"},
            json={"timezone": "America/New_York"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["timezone"] == "America/New_York"

    def test_update_invalid_timezone(self, client):
        """Should reject invalid timezone."""
        # Setup
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "badtz@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "badtz@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        # Update with invalid timezone
        response = client.patch(
            "/api/v1/users/me/preferences",
            headers={"Authorization": f"Bearer {token}"},
            json={"timezone": "Not/A/Timezone"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDeactivateAccount:
    """Tests for DELETE /api/v1/users/me."""

    def test_deactivate_account(self, client):
        """Should deactivate user account."""
        # Setup
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "deactivate@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "deactivate@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        # Deactivate
        response = client.delete(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Should not be able to login anymore
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "deactivate@example.com",
                "password": "SecurePass123",
            },
        )
        assert login_response.status_code == status.HTTP_401_UNAUTHORIZED
