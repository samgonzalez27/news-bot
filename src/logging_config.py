"""
Logging configuration for the News Digest API.

Provides stdout logging and rotating file handler for production use.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.config import get_settings


def setup_logging() -> logging.Logger:
    """
    Configure application logging with stdout and rotating file handlers.

    Returns:
        logging.Logger: Configured root logger for the application.
    """
    settings = get_settings()

    # Create logger
    logger = logging.getLogger("news_digest")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Clear existing handlers
    logger.handlers.clear()

    # Log format
    log_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(log_format)
    stdout_handler.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    logger.addHandler(stdout_handler)

    # Rotating file handler (only in production or if path exists)
    if settings.is_production or Path(settings.log_file_path).parent.exists():
        try:
            # Ensure log directory exists
            log_dir = Path(settings.log_file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                filename=settings.log_file_path,
                maxBytes=settings.log_max_bytes,
                backupCount=settings.log_backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(log_format)
            file_handler.setLevel(
                getattr(logging, settings.log_level.upper(), logging.INFO)
            )
            logger.addHandler(file_handler)
        except PermissionError:
            logger.warning(
                f"Cannot write to log file {settings.log_file_path}, "
                "using stdout only"
            )

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger with the specified name.

    Args:
        name: Name for the child logger (e.g., "auth_service").

    Returns:
        logging.Logger: Child logger instance.
    """
    return logging.getLogger(f"news_digest.{name}")
