"""Telemetry and observability utilities."""

from typing import Optional
from ..retrievers.base import RetrievalMetrics


async def log_retrieval_metrics(metrics: RetrievalMetrics) -> None:
    """Log retrieval metrics for observability.

    Args:
        metrics: Retrieval metrics to log
    """
    from .logging import get_logger

    logger = get_logger("deepagents_mcp_rag.retrieval")

    # Log basic metrics
    logger.info(
        f"Retrieval completed - Strategy: {metrics.strategy}, "
        f"Query: {metrics.query[:100]}{'...' if len(metrics.query) > 100 else ''}, "
        f"Results: {metrics.num_results}, "
        f"Latency: {metrics.latency_ms:.2f}ms, "
        f"Cache hit: {metrics.cache_hit}"
    )

    # Log to observability systems if configured
    await _log_to_phoenix(metrics)
    await _log_to_langsmith(metrics)


async def _log_to_phoenix(metrics: RetrievalMetrics) -> None:
    """Log metrics to Phoenix observability platform.

    Args:
        metrics: Retrieval metrics to log
    """
    try:
        # Phoenix integration would go here
        # For now, we'll just pass
        pass

    except Exception:
        # Don't fail retrieval due to observability issues
        pass


async def _log_to_langsmith(metrics: RetrievalMetrics) -> None:
    """Log metrics to LangSmith.

    Args:
        metrics: Retrieval metrics to log
    """
    try:
        # LangSmith integration would go here
        # For now, we'll just pass
        pass

    except Exception:
        # Don't fail retrieval due to observability issues
        pass