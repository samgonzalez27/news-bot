"""
Logging configuration for the News Digest API.

Provides structured JSON logging for production and human-readable logs for development.
Includes request-id tracking for distributed tracing.
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

from src.config import get_settings

# Context variable for request ID tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """Get the current request ID from context."""
    return request_id_var.get()


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set the request ID in context, generating one if not provided."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.
    
    Produces log entries in JSON format with consistent fields for
    easy parsing by log aggregation systems (ELK, CloudWatch, etc.).
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request ID if available
        request_id = get_request_id()
        if request_id:
            log_entry["request_id"] = request_id

        # Add extra fields from record
        if hasattr(record, "request_path"):
            log_entry["request_path"] = record.request_path
        if hasattr(record, "client_ip"):
            log_entry["client_ip"] = record.client_ip
        if hasattr(record, "method"):
            log_entry["method"] = record.method
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable console formatter for development.
    
    Colorized output with clear formatting for local development.
    """

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and readable structure."""
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Base format
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"{color}{timestamp} | {record.levelname:8s}{self.RESET} | {record.name}"
        
        # Add request ID if available
        request_id = get_request_id()
        if request_id:
            prefix += f" | req:{request_id[:8]}"
        
        message = record.getMessage()
        
        # Format exception if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return f"{prefix} | {message}"


def setup_logging() -> logging.Logger:
    """
    Configure application logging with appropriate handlers.

    In production (log_json_format=True): JSON formatted logs
    In development: Human-readable colored console output
    
    Returns:
        logging.Logger: Configured root logger for the application.
    """
    settings = get_settings()

    # Create logger
    logger = logging.getLogger("news_digest")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Clear existing handlers
    logger.handlers.clear()

    # Choose formatter based on settings
    if settings.log_json_format and settings.is_production:
        formatter = JSONFormatter()
    else:
        formatter = ConsoleFormatter()

    # Stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    logger.addHandler(stdout_handler)

    # Rotating file handler (production or if path exists)
    if settings.log_file_path and (
        settings.is_production or Path(settings.log_file_path).parent.exists()
    ):
        try:
            log_dir = Path(settings.log_file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                filename=settings.log_file_path,
                maxBytes=settings.log_max_bytes,
                backupCount=settings.log_backup_count,
                encoding="utf-8",
            )
            # Always use JSON format for file logs
            file_handler.setFormatter(JSONFormatter())
            file_handler.setLevel(
                getattr(logging, settings.log_level.upper(), logging.INFO)
            )
            logger.addHandler(file_handler)
        except PermissionError:
            logger.warning(
                f"Cannot write to log file {settings.log_file_path}, using stdout only"
            )

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger with the specified name.

    Args:
        name: Name for the child logger (e.g., "auth_service", "scheduler").

    Returns:
        logging.Logger: Child logger instance.
    """
    return logging.getLogger(f"news_digest.{name}")
