"""
core/logger.py

Loguru-based structured logging configuration.

Call ``setup_logging()`` once at application startup (inside the lifespan
context manager). After that, every module can simply do:

    from loguru import logger
    logger.info("My message")

The format and sink are controlled by the environment variables
``LOG_LEVEL``, ``LOG_FORMAT`` (``text`` | ``json``), and ``LOG_FILE_PATH``.
"""

from __future__ import annotations

import sys

from loguru import logger

from core.config import settings


def setup_logging() -> None:
    """
    Configure the global Loguru logger.

    - Removes the default stderr sink.
    - Adds a new stderr sink with the configured level and format.
    - Adds a rotating file sink so logs are also persisted to disk.
    """
    logger.remove()  # clear default handler

    # ── Console sink ──────────────────────────────────────────────────────────
    if settings.log_format == "json":
        fmt = (
            '{{"time":"{time:YYYY-MM-DDTHH:mm:ss.SSS}Z",'
            '"level":"{level}",'
            '"logger":"{name}",'
            '"message":"{message}",'
            '"extra":{extra}}}'
        )
        serialize = True
    else:
        fmt = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        serialize = False

    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=fmt,
        serialize=serialize,
        colorize=not serialize,
        backtrace=settings.debug,
        diagnose=settings.debug,
    )

    # ── File sink (always plain text for readability in log aggregators) ──────
    logger.add(
        settings.log_file_path,
        level=settings.log_level,
        rotation="50 MB",
        retention="14 days",
        compression="gz",
        encoding="utf-8",
        format=(
            "{time:YYYY-MM-DDTHH:mm:ss.SSS}Z | {level: <8} | "
            "{name}:{function}:{line} - {message}"
        ),
        backtrace=settings.debug,
        diagnose=settings.debug,
    )

    logger.info(
        "Logging configured: level={level}, format={fmt}, file={path}",
        level=settings.log_level,
        fmt=settings.log_format,
        path=settings.log_file_path,
    )
