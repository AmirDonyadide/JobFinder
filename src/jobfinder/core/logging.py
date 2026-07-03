"""Shared logging setup for command-line entry points."""

from __future__ import annotations

import logging
import os

DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
DEFAULT_DATE_FORMAT = "%H:%M:%S"


def configure_cli_logging(level: int | None = None) -> None:
    """Configure consistent human-readable logging for CLI commands."""
    if level is None:
        configured_level = os.environ.get("JOBFINDER_LOG_LEVEL", "INFO").upper()
        resolved_level = getattr(logging, configured_level, logging.INFO)
        level = resolved_level if isinstance(resolved_level, int) else logging.INFO
    logging.basicConfig(
        level=level,
        format=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
    )
