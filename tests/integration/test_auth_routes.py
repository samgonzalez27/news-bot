"""
Integration tests for authentication routes.
"""

import pytest
from fastapi import status


class TestRegisterEndpoint:
    """Tests for POST /api/v1/auth/register."""

    def test_register_success(self, client):
        """Should register a new user successfully."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123",
                "full_name": "New User",
                "preferred_time": "09:00",
                "timezone": "UTC",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_invalid_email(self, client):
        """Should reject invalid email format."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123",
                "full_name": "Test User",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_weak_password(self, client):
        """Should reject password without letters and numbers."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "nodigits",
                "full_name": "Test User",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_short_password(self, client):
        """Should reject password shorter than 8 characters."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "Ab1",
                "full_name": "Test User",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_invalid_timezone(self, client):
        """Should reject invalid timezone."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
                "timezone": "Invalid/Timezone",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_invalid_time_format(self, client):
        """Should reject invalid time format."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
                "preferred_time": "25:00",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_duplicate_email(self, client):
        """Should reject duplicate email."""
        user_data = {
            "email": "duplicate@example.com",
            "password": "SecurePass123",
            "full_name": "First User",
        }

        # First registration
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED

        # Duplicate registration
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_409_CONFLICT


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login."""

    def test_login_success(self, client):
        """Should login successfully with valid credentials."""
        # Register first
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "SecurePass123",
                "full_name": "Login User",
            },
        )

        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_invalid_email(self, client):
        """Should reject login with non-existent email."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_wrong_password(self, client):
        """Should reject login with wrong password."""
        # Register first
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "CorrectPass123",
                "full_name": "Test User",
            },
        )

        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "WrongPass456",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_case_insensitive_email(self, client):
        """Should handle email case-insensitively."""
        # Register with lowercase
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "case@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
            },
        )

        # Login with uppercase
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "CASE@EXAMPLE.COM",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == status.HTTP_200_OK
