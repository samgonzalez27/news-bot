"""
Unit tests for logging_config module.
"""

import pytest
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.logging_config import setup_logging, get_logger


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_creates_logger(self):
        """Should create and return a logger."""
        with patch("src.logging_config.get_settings") as mock_settings:
            mock_settings.return_value.log_level = "INFO"
            mock_settings.return_value.is_production = False
            mock_settings.return_value.log_file_path = "/nonexistent/path/app.log"
            
            logger = setup_logging()
            
            assert logger is not None
            assert logger.name == "news_digest"

    def test_sets_log_level(self):
        """Should set log level from settings."""
        with patch("src.logging_config.get_settings") as mock_settings:
            mock_settings.return_value.log_level = "DEBUG"
            mock_settings.return_value.is_production = False
            mock_settings.return_value.log_file_path = "/nonexistent/path/app.log"
            
            logger = setup_logging()
            
            assert logger.level == logging.DEBUG

    def test_adds_stdout_handler(self):
        """Should add stdout handler."""
        with patch("src.logging_config.get_settings") as mock_settings:
            mock_settings.return_value.log_level = "INFO"
            mock_settings.return_value.is_production = False
            mock_settings.return_value.log_file_path = "/nonexistent/path/app.log"
            
            logger = setup_logging()
            
            assert len(logger.handlers) >= 1
            assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_adds_file_handler_in_production(self):
        """Should add file handler in production mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "app.log"
            
            with patch("src.logging_config.get_settings") as mock_settings:
                mock_settings.return_value.log_level = "INFO"
                mock_settings.return_value.is_production = True
                mock_settings.return_value.log_file_path = str(log_path)
                mock_settings.return_value.log_max_bytes = 1024
                mock_settings.return_value.log_backup_count = 1
                
                logger = setup_logging()
                
                # Should have file handler
                from logging.handlers import RotatingFileHandler
                assert any(isinstance(h, RotatingFileHandler) for h in logger.handlers)

    def test_handles_permission_error(self):
        """Should handle permission error gracefully."""
        with patch("src.logging_config.get_settings") as mock_settings:
            mock_settings.return_value.log_level = "INFO"
            mock_settings.return_value.is_production = True
            mock_settings.return_value.log_file_path = "/root/nopermission/app.log"
            mock_settings.return_value.log_max_bytes = 1024
            mock_settings.return_value.log_backup_count = 1
            
            # This might succeed if running as root, but should not crash
            logger = setup_logging()
            assert logger is not None


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_child_logger(self):
        """Should return a child logger with proper name."""
        logger = get_logger("test_module")
        
        assert logger.name == "news_digest.test_module"

    def test_multiple_calls_same_name(self):
        """Should return same logger for same name."""
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        
        assert logger1 is logger2
