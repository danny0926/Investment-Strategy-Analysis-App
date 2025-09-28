"""Logging configuration using structlog."""
from __future__ import annotations

import logging
from typing import Any, Dict

import structlog


def configure_logging() -> None:
    """Configure structlog for JSON-style logs."""

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            timestamper,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> "structlog.BoundLogger":
    """Return a configured logger."""

    return structlog.get_logger(name)
