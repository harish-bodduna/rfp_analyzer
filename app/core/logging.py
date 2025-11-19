"""Logging utilities."""
import logging
from logging.config import dictConfig

from app.core.config import settings


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "root": {"handlers": ["console"], "level": settings.log_level},
}


def configure_logging() -> None:
    """Apply logging configuration once at startup."""

    dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """Shortcut to configure and fetch a logger."""

    if not logging.getLogger().handlers:
        configure_logging()
    return logging.getLogger(name)
