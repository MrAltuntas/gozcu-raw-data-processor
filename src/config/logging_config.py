"""Logging configuration"""
import logging
import sys
from src.config.settings import settings


def setup_logging() -> None:
    """
    Configure application logging with proper format and level.

    Sets up console logging with structured format including:
    - Timestamp
    - Log level
    - Logger name
    - Message
    """
    log_level = getattr(logging, settings.log.log_level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Reduce noise from external libraries
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)

    logging.info(f"Logging configured with level: {settings.log.log_level.upper()}")
