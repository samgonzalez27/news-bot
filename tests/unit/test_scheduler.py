"""
Unit tests for scheduler module.
"""

from unittest.mock import patch, PropertyMock

from src.scheduler.scheduler import (
    scheduler,
    start_scheduler,
    stop_scheduler,
)


class TestStartScheduler:
    """Tests for start_scheduler function."""

    def test_disabled_by_config(self):
        """Should not start when disabled by configuration."""
        with patch("src.scheduler.scheduler.get_settings") as mock_settings:
            mock_settings.return_value.scheduler_enabled = False
            
            start_scheduler()
            
            # Scheduler should not be running
            # (We just verify no exceptions were raised)

    def test_already_running(self):
        """Should log warning when already running."""
        with patch("src.scheduler.scheduler.get_settings") as mock_settings:
            mock_settings.return_value.scheduler_enabled = True
            
            with patch.object(type(scheduler), "running", new_callable=PropertyMock, return_value=True):
                # Should not raise even if already running
                start_scheduler()

    def test_starts_successfully(self):
        """Should start scheduler when enabled."""
        with patch("src.scheduler.scheduler.get_settings") as mock_settings:
            mock_settings.return_value.scheduler_enabled = True
            mock_settings.return_value.digest_check_interval_minutes = 15
            
            with patch.object(type(scheduler), "running", new_callable=PropertyMock, return_value=False):
                with patch.object(scheduler, "start") as mock_start:
                    with patch("src.scheduler.jobs.schedule_digest_jobs"):
                        start_scheduler()
                        mock_start.assert_called_once()


class TestStopScheduler:
    """Tests for stop_scheduler function."""

    def test_stops_running_scheduler(self):
        """Should stop scheduler when running."""
        with patch.object(type(scheduler), "running", new_callable=PropertyMock, return_value=True):
            with patch.object(scheduler, "shutdown") as mock_shutdown:
                stop_scheduler()
                mock_shutdown.assert_called_once_with(wait=True)

    def test_does_nothing_when_not_running(self):
        """Should do nothing when scheduler is not running."""
        with patch.object(type(scheduler), "running", new_callable=PropertyMock, return_value=False):
            with patch.object(scheduler, "shutdown") as mock_shutdown:
                stop_scheduler()
                mock_shutdown.assert_not_called()
