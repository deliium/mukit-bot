"""Utility functions for the bot."""

import logging

from config import LOG_FORMAT, LOG_LEVEL


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        format=LOG_FORMAT,
        level=getattr(logging, LOG_LEVEL.upper()),
    )

