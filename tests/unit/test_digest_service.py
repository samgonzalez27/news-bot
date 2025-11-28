"""
Unit tests for the digest service.
"""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

import pytest

from src.models.digest import Digest, DigestStatus
from src.services.digest_service import DigestService
from src.exceptions import NotFoundError


class TestDigestService:
    """Tests for DigestService functionality."""

    @pytest.mark.asyncio
    async def test_get_digest_by_id(self, seeded_db, test_user):
        """Should retrieve digest by ID."""
        # Create a digest
        digest = Digest(
            id=uuid4(),
            user_id=test_user.id,
            digest_date=date.today() - timedelta(days=1),
            content="Test digest content",
            status=DigestStatus.COMPLETED.value,
        )
        seeded_db.add(digest)
        await seeded_db.commit()

        # Retrieve it
        service = DigestService(seeded_db)
        result = await service.get_digest_by_id(digest.id)

        assert result is not None
        assert result.id == digest.id

    @pytest.mark.asyncio
    async def test_get_digest_by_id_with_user_check(self, seeded_db, test_user):
        """Should only return digest if user matches."""
        digest = Digest(
            id=uuid4(),
            user_id=test_user.id,
            digest_date=date.today() - timedelta(days=1),
            content="Test content",
            status=DigestStatus.COMPLETED.value,
        )
        seeded_db.add(digest)
        await seeded_db.commit()

        service = DigestService(seeded_db)

        # With correct user
        result = await service.get_digest_by_id(digest.id, test_user.id)
        assert result is not None

        # With wrong user
        wrong_user_id = uuid4()
        result = await service.get_digest_by_id(digest.id, wrong_user_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_digest_by_date(self, seeded_db, test_user):
        """Should retrieve digest by date."""
        target_date = date.today() - timedelta(days=1)
        digest = Digest(
            id=uuid4(),
            user_id=test_user.id,
            digest_date=target_date,
            content="Test content",
            status=DigestStatus.COMPLETED.value,
        )
        seeded_db.add(digest)
        await seeded_db.commit()

        service = DigestService(seeded_db)
        result = await service.get_digest_by_date(test_user.id, target_date)

        assert result is not None
        assert result.digest_date == target_date

    @pytest.mark.asyncio
    async def test_get_user_digests_pagination(self, seeded_db, test_user):
        """Should return paginated digest list."""
        # Create multiple digests
        for i in range(5):
            digest = Digest(
                id=uuid4(),
                user_id=test_user.id,
                digest_date=date.today() - timedelta(days=i + 1),
                content=f"Digest content {i}",
                status=DigestStatus.COMPLETED.value,
            )
            seeded_db.add(digest)
        await seeded_db.commit()

        service = DigestService(seeded_db)

        # First page
        result = await service.get_user_digests(test_user.id, page=1, per_page=2)

        assert result["total"] == 5
        assert len(result["digests"]) == 2
        assert result["page"] == 1
        assert result["per_page"] == 2
        assert result["has_next"] is True

        # Last page
        result = await service.get_user_digests(test_user.id, page=3, per_page=2)

        assert len(result["digests"]) == 1
        assert result["has_next"] is False

    @pytest.mark.asyncio
    async def test_get_latest_digest(self, seeded_db, test_user):
        """Should return most recent digest."""
        # Create digests with different dates
        for i in range(3):
            digest = Digest(
                id=uuid4(),
                user_id=test_user.id,
                digest_date=date.today() - timedelta(days=i + 1),
                content=f"Digest {i}",
                status=DigestStatus.COMPLETED.value,
            )
            seeded_db.add(digest)
        await seeded_db.commit()

        service = DigestService(seeded_db)
        result = await service.get_latest_digest(test_user.id)

        assert result is not None
        assert result.digest_date == date.today() - timedelta(days=1)

    @pytest.mark.asyncio
    async def test_get_latest_digest_no_digests(self, seeded_db, test_user):
        """Should return None when no digests exist."""
        service = DigestService(seeded_db)
        result = await service.get_latest_digest(test_user.id)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_digest(self, seeded_db, test_user):
        """Should delete digest."""
        digest = Digest(
            id=uuid4(),
            user_id=test_user.id,
            digest_date=date.today() - timedelta(days=1),
            content="Test content",
            status=DigestStatus.COMPLETED.value,
        )
        seeded_db.add(digest)
        await seeded_db.commit()

        service = DigestService(seeded_db)
        result = await service.delete_digest(digest.id, test_user.id)

        assert result is True

        # Verify deleted
        deleted = await service.get_digest_by_id(digest.id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_delete_digest_wrong_user(self, seeded_db, test_user):
        """Should not delete digest for wrong user."""
        digest = Digest(
            id=uuid4(),
            user_id=test_user.id,
            digest_date=date.today() - timedelta(days=1),
            content="Test content",
            status=DigestStatus.COMPLETED.value,
        )
        seeded_db.add(digest)
        await seeded_db.commit()

        service = DigestService(seeded_db)
        wrong_user_id = uuid4()
        result = await service.delete_digest(digest.id, wrong_user_id)

        assert result is False

        # Verify not deleted
        existing = await service.get_digest_by_id(digest.id)
        assert existing is not None

    @pytest.mark.asyncio
    async def test_generate_digest_no_interests(self, seeded_db, test_user):
        """Should create placeholder digest when user has no interests."""
        service = DigestService(seeded_db)

        with patch(
            "src.services.digest_service.InterestService"
        ) as MockInterestService:
            mock_instance = MagicMock()
            mock_instance.get_user_interests = AsyncMock(return_value=[])
            MockInterestService.return_value = mock_instance

            digest = await service.generate_digest(test_user.id)

            assert digest is not None
            assert "No interests selected" in digest.content
            assert digest.status == DigestStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_generate_digest_existing_not_force(self, seeded_db, test_user):
        """Should return existing digest when not forcing regeneration."""
        target_date = date.today() - timedelta(days=1)
        existing_digest = Digest(
            id=uuid4(),
            user_id=test_user.id,
            digest_date=target_date,
            content="Existing content",
            status=DigestStatus.COMPLETED.value,
        )
        seeded_db.add(existing_digest)
        await seeded_db.commit()

        service = DigestService(seeded_db)
        result = await service.generate_digest(
            test_user.id,
            digest_date=target_date,
            force=False,
        )

        assert result.id == existing_digest.id
        assert result.content == "Existing content"
