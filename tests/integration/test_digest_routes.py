"""
Integration tests for digest routes.
"""

from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi import status


class TestListDigests:
    """Tests for GET /api/v1/digests."""

    def test_list_digests_empty(self, client):
        """Should return empty list for new user."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "nodig@example.com",
                "password": "SecurePass123",
                "full_name": "No Digests",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nodig@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/digests",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["digests"] == []
        assert data["total"] == 0

    def test_list_digests_requires_auth(self, client):
        """Should require authentication."""
        response = client.get("/api/v1/digests")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_digests_pagination_params(self, client):
        """Should accept pagination parameters."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "pagdig@example.com",
                "password": "SecurePass123",
                "full_name": "Pagination Digests",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "pagdig@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/digests?page=1&per_page=5",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 5


class TestGetLatestDigest:
    """Tests for GET /api/v1/digests/latest."""

    def test_get_latest_no_digests(self, client):
        """Should return 404 when no digests exist."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "nolat@example.com",
                "password": "SecurePass123",
                "full_name": "No Latest",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nolat@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/digests/latest",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGenerateDigest:
    """Tests for POST /api/v1/digests/generate."""

    def test_generate_digest_no_interests(self, client):
        """Should create placeholder when user has no interests."""
        # Setup user without interests
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "gennoints@example.com",
                "password": "SecurePass123",
                "full_name": "Gen No Interests",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "gennoints@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        response = client.post(
            "/api/v1/digests/generate",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "No interests selected" in data["content"]

    def test_generate_digest_requires_auth(self, client):
        """Should require authentication."""
        response = client.post("/api/v1/digests/generate")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetDigestByDate:
    """Tests for GET /api/v1/digests/by-date/{date}."""

    def test_get_digest_by_date_not_found(self, client):
        """Should return 404 for non-existent date."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "datedig@example.com",
                "password": "SecurePass123",
                "full_name": "Date Digest",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "datedig@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/digests/by-date/2024-01-15",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_digest_by_date_invalid_format(self, client):
        """Should reject invalid date format."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "baddate@example.com",
                "password": "SecurePass123",
                "full_name": "Bad Date",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "baddate@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/digests/by-date/not-a-date",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
