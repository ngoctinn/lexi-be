"""
Logging configuration for Lexi application.
Provides structured logging with JSON format for CloudWatch.
"""

import json
import logging
from datetime import datetime, timezone
from logging.config import dictConfig
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from infrastructure.configuration.config import Config


class JsonLogEncoder(json.JSONEncoder):
    """Custom JSON encoder for log records."""

    def default(self, o: Any) -> Any:
        """Handle non-serializable types."""
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, UUID):
            return str(o)
        if isinstance(o, set):
            return list(o)
        if isinstance(o, Exception):
            return str(o)
        return super().default(o)


class JsonFormatter(logging.Formatter):
    """Formats log records as JSON for CloudWatch."""

    def __init__(self, app_context: str = "lambda"):
        super().__init__()
        self.app_context = app_context
        self.encoder = JsonLogEncoder()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.now(timezone.utc),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "app_context": self.app_context,
        }

        # Add extra context if provided
        context = {}
        for key, value in record.__dict__.items():
            if key == "context":
                context = value
                break

        if context:
            log_data["context"] = context

        return self.encoder.encode(log_data)


def configure_logging(app_context: Literal["lambda", "cli"] = "lambda") -> None:
    """
    Configure application logging.

    Args:
        app_context: Application context (lambda or cli)
    """
    log_dir = Config.get_log_dir()

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JsonFormatter,
                "app_context": app_context,
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if app_context == "lambda" else "standard",
                "level": Config.LOG_LEVEL,
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": log_dir / "app.log",
                "formatter": "json",
                "level": Config.LOG_LEVEL,
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": Config.LOG_LEVEL,
                "propagate": True,
            },
            "application": {
                "level": Config.LOG_LEVEL,
            },
            "domain": {
                "level": Config.LOG_LEVEL,
            },
            "infrastructure": {
                "level": Config.LOG_LEVEL,
            },
            "interfaces": {
                "level": Config.LOG_LEVEL,
            },
        },
    }

    dictConfig(config)
