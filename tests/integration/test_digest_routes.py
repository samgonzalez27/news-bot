"""
Integration tests for digest routes.
"""

from datetime import date, timedelta
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

    def test_get_latest_digest_success(self, client):
        """Should return latest digest when available."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "haslat@example.com",
                "password": "SecurePass123",
                "full_name": "Has Latest",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "haslat@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Generate a digest first
        client.post("/api/v1/digests/generate", headers=headers)

        # Get latest
        response = client.get("/api/v1/digests/latest", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "digest_date" in data


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

    def test_generate_digest_with_date(self, client):
        """Should generate digest for specific date."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "gendate@example.com",
                "password": "SecurePass123",
                "full_name": "Gen Date",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "gendate@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        target_date = (date.today() - timedelta(days=2)).isoformat()
        response = client.post(
            "/api/v1/digests/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"digest_date": target_date},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["digest_date"] == target_date


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

    def test_get_digest_by_date_found(self, client):
        """Should return digest when it exists for date."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "founddate@example.com",
                "password": "SecurePass123",
                "full_name": "Found Date",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "founddate@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Generate a digest first
        gen_response = client.post("/api/v1/digests/generate", headers=headers)
        digest_date = gen_response.json()["digest_date"]

        # Get by date
        response = client.get(f"/api/v1/digests/by-date/{digest_date}", headers=headers)

        assert response.status_code == status.HTTP_200_OK


class TestGetDigestById:
    """Tests for GET /api/v1/digests/{digest_id}."""

    def test_get_digest_by_id_not_found(self, client):
        """Should return 404 for non-existent ID."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "iddig@example.com",
                "password": "SecurePass123",
                "full_name": "ID Digest",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "iddig@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/digests/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_digest_by_id_found(self, client):
        """Should return digest when it exists."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "foundid@example.com",
                "password": "SecurePass123",
                "full_name": "Found ID",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "foundid@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Generate a digest first
        gen_response = client.post("/api/v1/digests/generate", headers=headers)
        digest_id = gen_response.json()["id"]

        # Get by ID
        response = client.get(f"/api/v1/digests/{digest_id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK


class TestRegenerateDigest:
    """Tests for POST /api/v1/digests/regenerate/{date}."""

    def test_regenerate_digest_success(self, client):
        """Should regenerate digest for a date."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "regen@example.com",
                "password": "SecurePass123",
                "full_name": "Regen User",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "regen@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Generate initial digest
        gen_response = client.post("/api/v1/digests/generate", headers=headers)
        digest_date = gen_response.json()["digest_date"]

        # Regenerate
        response = client.post(f"/api/v1/digests/regenerate/{digest_date}", headers=headers)

        assert response.status_code == status.HTTP_200_OK

    def test_regenerate_requires_auth(self, client):
        """Should require authentication."""
        response = client.post("/api/v1/digests/regenerate/2024-01-15")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteDigest:
    """Tests for DELETE /api/v1/digests/{digest_id}."""

    def test_delete_digest_success(self, client):
        """Should delete existing digest."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "deldig@example.com",
                "password": "SecurePass123",
                "full_name": "Del Digest",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "deldig@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Generate a digest first
        gen_response = client.post("/api/v1/digests/generate", headers=headers)
        digest_id = gen_response.json()["id"]

        # Delete
        response = client.delete(f"/api/v1/digests/{digest_id}", headers=headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_digest_not_found(self, client):
        """Should return 404 for non-existent ID."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "delnf@example.com",
                "password": "SecurePass123",
                "full_name": "Del Not Found",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "delnf@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        response = client.delete(
            "/api/v1/digests/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_requires_auth(self, client):
        """Should require authentication."""
        response = client.delete("/api/v1/digests/00000000-0000-0000-0000-000000000000")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
