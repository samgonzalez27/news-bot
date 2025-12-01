"""
End-to-end tests for complete user flows.

These tests simulate real user scenarios from registration
through digest generation and consumption.
"""

from fastapi import status


class TestCompleteUserJourney:
    """
    Tests the complete user journey from registration to receiving digests.
    
    Flow:
    1. User registers
    2. User logs in
    3. User selects interests
    4. User triggers digest generation
    5. User views their digest
    """

    def test_full_journey_success(self, client):
        """Complete journey from registration to digest viewing."""
        # Step 1: Register
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "journey@example.com",
                "password": "SecurePass123",
                "full_name": "Journey User",
                "preferred_time": "07:00",
                "timezone": "America/Los_Angeles",
            },
        )
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["id"]

        # Step 2: Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "journey@example.com",
                "password": "SecurePass123",
            },
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 3: View available interests
        interests_response = client.get("/api/v1/interests")
        assert interests_response.status_code == status.HTTP_200_OK
        available_interests = interests_response.json()["interests"]
        assert len(available_interests) > 0

        # Step 4: Subscribe to interests
        subscribe_response = client.put(
            "/api/v1/interests/me",
            headers=headers,
            json={"interest_slugs": ["technology", "science"]},
        )
        assert subscribe_response.status_code == status.HTTP_200_OK
        assert len(subscribe_response.json()) == 2

        # Step 5: Verify profile shows interests
        profile_response = client.get("/api/v1/users/me", headers=headers)
        assert profile_response.status_code == status.HTTP_200_OK
        profile = profile_response.json()
        assert len(profile["interests"]) == 2

        # Step 6: Generate a digest (mocking external APIs)
        generate_response = client.post(
            "/api/v1/digests/generate",
            headers=headers,
        )
        assert generate_response.status_code == status.HTTP_201_CREATED
        digest = generate_response.json()
        assert digest["user_id"] == user_id

        # Step 7: View digests list
        digests_response = client.get("/api/v1/digests", headers=headers)
        assert digests_response.status_code == status.HTTP_200_OK
        assert digests_response.json()["total"] >= 1

        # Step 8: Get latest digest
        latest_response = client.get("/api/v1/digests/latest", headers=headers)
        assert latest_response.status_code == status.HTTP_200_OK


class TestInterestManagementFlow:
    """Tests various interest management scenarios."""

    def test_add_remove_interests_individually(self, client):
        """User can add and remove interests one at a time."""
        # Setup
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "intflow@example.com",
                "password": "SecurePass123",
                "full_name": "Interest Flow",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "intflow@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Add technology
        resp1 = client.post("/api/v1/interests/me/technology", headers=headers)
        assert resp1.status_code == status.HTTP_201_CREATED

        # Add science
        resp2 = client.post("/api/v1/interests/me/science", headers=headers)
        assert resp2.status_code == status.HTTP_201_CREATED

        # Verify both exist
        my_interests = client.get("/api/v1/interests/me", headers=headers).json()
        assert len(my_interests) == 2

        # Remove technology
        resp3 = client.delete("/api/v1/interests/me/technology", headers=headers)
        assert resp3.status_code == status.HTTP_204_NO_CONTENT

        # Verify only science remains
        my_interests = client.get("/api/v1/interests/me", headers=headers).json()
        assert len(my_interests) == 1
        assert my_interests[0]["slug"] == "science"


class TestPreferencesFlow:
    """Tests user preferences update scenarios."""

    def test_update_all_preferences(self, client):
        """User can update all preferences at once."""
        # Setup
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "prefsflow@example.com",
                "password": "SecurePass123",
                "full_name": "Prefs Flow",
                "preferred_time": "08:00",
                "timezone": "UTC",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "prefsflow@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Update preferences
        update_response = client.patch(
            "/api/v1/users/me/preferences",
            headers=headers,
            json={
                "preferred_time": "19:30",
                "timezone": "Europe/London",
            },
        )
        assert update_response.status_code == status.HTTP_200_OK
        data = update_response.json()
        assert data["preferred_time"] == "19:30"
        assert data["timezone"] == "Europe/London"

        # Verify changes persisted
        profile = client.get("/api/v1/users/me", headers=headers).json()
        assert profile["preferred_time"] == "19:30"
        assert profile["timezone"] == "Europe/London"


class TestDigestHistoryFlow:
    """Tests digest history viewing scenarios."""

    def test_multiple_digests_pagination(self, client):
        """User can paginate through multiple digests."""
        from datetime import date, timedelta
        
        # Setup user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "dighistory@example.com",
                "password": "SecurePass123",
                "full_name": "Digest History",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "dighistory@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Generate multiple digests for different dates
        today = date.today()
        for i in range(1, 4):
            digest_date = (today - timedelta(days=i)).isoformat()
            client.post(
                "/api/v1/digests/generate",
                headers=headers,
                json={"digest_date": digest_date},
            )

        # Test pagination - page 1
        page1 = client.get("/api/v1/digests?page=1&per_page=2", headers=headers).json()
        assert page1["page"] == 1
        assert page1["per_page"] == 2
        assert len(page1["digests"]) == 2
        assert page1["total"] >= 3

        # Test pagination - page 2
        page2 = client.get("/api/v1/digests?page=2&per_page=2", headers=headers).json()
        assert page2["page"] == 2
        assert len(page2["digests"]) >= 1


class TestAccountLifecycle:
    """Tests account creation, modification, and deactivation."""

    def test_full_account_lifecycle(self, client):
        """User can register, modify profile, and deactivate account."""
        # Register
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "lifecycle@example.com",
                "password": "SecurePass123",
                "full_name": "Lifecycle User",
            },
        )
        assert register_response.status_code == status.HTTP_201_CREATED

        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "lifecycle@example.com",
                "password": "SecurePass123",
            },
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Update profile
        update_response = client.patch(
            "/api/v1/users/me",
            headers=headers,
            json={"full_name": "Updated Lifecycle User"},
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["full_name"] == "Updated Lifecycle User"

        # Deactivate
        delete_response = client.delete("/api/v1/users/me", headers=headers)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify cannot login
        login_attempt = client.post(
            "/api/v1/auth/login",
            json={
                "email": "lifecycle@example.com",
                "password": "SecurePass123",
            },
        )
        assert login_attempt.status_code == status.HTTP_401_UNAUTHORIZED


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
