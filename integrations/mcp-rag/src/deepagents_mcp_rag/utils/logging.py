"""Logging utilities for the DeepAgents MCP RAG system."""

import logging
import sys
from typing import Optional
from ..config import get_settings


def setup_logging(log_level: Optional[str] = None) -> None:
    """Setup logging configuration.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    if log_level is None:
        settings = get_settings()
        log_level = settings.log_level

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set specific loggers to appropriate levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)