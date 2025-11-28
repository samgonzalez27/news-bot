"""
Integration tests for interest routes.
"""

import pytest
from fastapi import status


class TestListInterests:
    """Tests for GET /api/v1/interests."""

    def test_list_interests_success(self, client):
        """Should return list of all interests."""
        response = client.get("/api/v1/interests")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "interests" in data
        assert "total" in data
        assert data["total"] > 0

    def test_list_interests_structure(self, client):
        """Should return interests with correct structure."""
        response = client.get("/api/v1/interests")
        data = response.json()

        interest = data["interests"][0]
        assert "id" in interest
        assert "name" in interest
        assert "slug" in interest
        assert "is_active" in interest


class TestGetMyInterests:
    """Tests for GET /api/v1/interests/me."""

    def test_get_my_interests_empty(self, client):
        """Should return empty list for new user."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "noint@example.com",
                "password": "SecurePass123",
                "full_name": "No Interests",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "noint@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/interests/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_my_interests_requires_auth(self, client):
        """Should require authentication."""
        response = client.get("/api/v1/interests/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateMyInterests:
    """Tests for PUT /api/v1/interests/me."""

    def test_update_interests_success(self, client):
        """Should update user's interests."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "intupdate@example.com",
                "password": "SecurePass123",
                "full_name": "Interest Update",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "intupdate@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        # Update interests
        response = client.put(
            "/api/v1/interests/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"interest_slugs": ["technology", "economics"]},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        slugs = [i["slug"] for i in data]
        assert "technology" in slugs
        assert "economics" in slugs

    def test_update_interests_replaces_all(self, client):
        """Should replace all existing interests."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "intreplace@example.com",
                "password": "SecurePass123",
                "full_name": "Interest Replace",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "intreplace@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Set initial interests
        client.put(
            "/api/v1/interests/me",
            headers=headers,
            json={"interest_slugs": ["technology", "economics"]},
        )

        # Replace with new interests
        response = client.put(
            "/api/v1/interests/me",
            headers=headers,
            json={"interest_slugs": ["sports"]},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["slug"] == "sports"

    def test_update_interests_invalid_slug(self, client):
        """Should reject invalid interest slugs."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "intinvalid@example.com",
                "password": "SecurePass123",
                "full_name": "Invalid Interest",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "intinvalid@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        response = client.put(
            "/api/v1/interests/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"interest_slugs": ["nonexistent-interest"]},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAddSingleInterest:
    """Tests for POST /api/v1/interests/me/{slug}."""

    def test_add_interest_success(self, client):
        """Should add a single interest."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "intadd@example.com",
                "password": "SecurePass123",
                "full_name": "Add Interest",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "intadd@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        response = client.post(
            "/api/v1/interests/me/technology",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["slug"] == "technology"

    def test_add_interest_invalid_slug(self, client):
        """Should reject invalid interest slug."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "intbadslug@example.com",
                "password": "SecurePass123",
                "full_name": "Bad Slug Interest",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "intbadslug@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        response = client.post(
            "/api/v1/interests/me/nonexistent-slug",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_add_interest_already_exists(self, client):
        """Should handle adding already-subscribed interest."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "intdup@example.com",
                "password": "SecurePass123",
                "full_name": "Dup Interest",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "intdup@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Add twice
        client.post("/api/v1/interests/me/technology", headers=headers)
        response = client.post("/api/v1/interests/me/technology", headers=headers)

        assert response.status_code == status.HTTP_201_CREATED


class TestRemoveSingleInterest:
    """Tests for DELETE /api/v1/interests/me/{slug}."""

    def test_remove_interest_success(self, client):
        """Should remove a single interest."""
        # Setup user with interest
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "intremove@example.com",
                "password": "SecurePass123",
                "full_name": "Remove Interest",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "intremove@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Add then remove
        client.post("/api/v1/interests/me/technology", headers=headers)
        response = client.delete("/api/v1/interests/me/technology", headers=headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify removed
        interests = client.get("/api/v1/interests/me", headers=headers).json()
        assert len(interests) == 0

    def test_remove_interest_invalid_slug(self, client):
        """Should reject removing non-existent interest slug."""
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "intrembad@example.com",
                "password": "SecurePass123",
                "full_name": "Remove Bad Interest",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "intrembad@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]

        response = client.delete(
            "/api/v1/interests/me/nonexistent-slug",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
