"""MCP Resources implementation - Query pattern for fast document retrieval."""

import time
from typing import Dict, Any, List, Optional
from urllib.parse import unquote

from ..retrievers.factory import RetrieverFactory


async def retrieval_resource(strategy: str, query: str) -> Dict[str, Any]:
    """Fast document retrieval without synthesis for MCP resource access.

    This implements the query pattern providing raw document access
    for 3-5x faster performance when synthesis isn't needed.

    URI Pattern: retriever://{strategy}/{query}

    Args:
        strategy: Retrieval strategy (bm25, vector, parent_doc, multi_query, rerank, ensemble)
        query: URL-encoded search query

    Returns:
        Raw documents with metadata for agent consumption
    """
    from ..utils.logging import get_logger

    logger = get_logger(__name__)
    start_time = time.time()

    # Decode URL-encoded query
    decoded_query = unquote(query)

    try:
        # Step 1: Create retriever for the specified strategy
        retriever = RetrieverFactory.create(strategy, k=10)  # Default to 10 for resources

        # Step 2: Execute fast retrieval
        logger.info(f"Resource retrieval - Strategy: {strategy}, Query: {decoded_query[:100]}...")

        documents = await retriever.retrieve(decoded_query)

        # Step 3: Format response for resource consumption
        retrieval_time = time.time() - start_time

        return {
            "documents": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "rank": i + 1
                }
                for i, doc in enumerate(documents)
            ],
            "query": decoded_query,
            "strategy": strategy,
            "num_results": len(documents),
            "retrieval_time_ms": round(retrieval_time * 1000, 2),
            "timestamp": time.time(),
            "resource_type": "retrieval"
        }

    except Exception as e:
        logger.error(f"Resource retrieval failed - Strategy: {strategy}, Error: {e}")
        return {
            "error": str(e),
            "query": decoded_query,
            "strategy": strategy,
            "retrieval_time_ms": round((time.time() - start_time) * 1000, 2),
            "resource_type": "retrieval"
        }


async def strategy_info_resource() -> Dict[str, Any]:
    """Get information about available retrieval strategies.

    URI Pattern: strategies://info

    Returns:
        Information about all available retrieval strategies
    """
    try:
        strategies_info = RetrieverFactory.list_strategies()

        return {
            "available_strategies": list(strategies_info.keys()),
            "strategy_details": strategies_info,
            "recommendations": {
                "factual_queries": "bm25",
                "conceptual_queries": "vector",
                "technical_queries": "parent_doc",
                "comprehensive_research": "ensemble",
                "high_precision": "rerank",
                "broad_coverage": "multi_query"
            },
            "performance_characteristics": {
                "fastest": ["bm25", "vector"],
                "most_accurate": ["rerank", "ensemble"],
                "best_context": ["parent_doc", "multi_query"],
                "balanced": ["ensemble", "vector"]
            },
            "resource_type": "strategy_info",
            "timestamp": time.time()
        }

    except Exception as e:
        return {
            "error": str(e),
            "resource_type": "strategy_info",
            "timestamp": time.time()
        }


async def collection_stats_resource(collection_name: str = "deepagents_documents") -> Dict[str, Any]:
    """Get statistics about a document collection.

    URI Pattern: collection://{collection_name}/stats

    Args:
        collection_name: Name of the collection

    Returns:
        Collection statistics and health information
    """
    from ..utils.vector_store import get_collection_info
    from ..utils.document_store import get_document_store

    try:
        # Get vector store statistics
        vector_stats = await get_collection_info(collection_name)

        # Get document store statistics
        doc_store = await get_document_store()
        doc_stats = await doc_store.get_stats()

        return {
            "collection_name": collection_name,
            "vector_store": vector_stats,
            "document_store": doc_stats,
            "health_status": "healthy" if not vector_stats.get("error") else "degraded",
            "last_updated": time.time(),
            "resource_type": "collection_stats"
        }

    except Exception as e:
        return {
            "error": str(e),
            "collection_name": collection_name,
            "health_status": "error",
            "resource_type": "collection_stats",
            "timestamp": time.time()
        }


async def cache_stats_resource() -> Dict[str, Any]:
    """Get cache performance statistics.

    URI Pattern: cache://stats

    Returns:
        Cache hit rates and performance metrics
    """
    from ..utils.cache import get_cache_client

    try:
        cache = await get_cache_client()
        stats = await cache.get_stats()

        return {
            "cache_stats": stats,
            "performance_summary": {
                "hit_rate_percentage": round(stats.get("hit_rate", 0) * 100, 2),
                "total_operations": stats.get("hits", 0) + stats.get("misses", 0),
                "memory_usage": stats.get("used_memory_human", "Unknown")
            },
            "recommendations": _generate_cache_recommendations(stats),
            "resource_type": "cache_stats",
            "timestamp": time.time()
        }

    except Exception as e:
        return {
            "error": str(e),
            "resource_type": "cache_stats",
            "timestamp": time.time()
        }


def _generate_cache_recommendations(stats: Dict[str, Any]) -> List[str]:
    """Generate cache optimization recommendations.

    Args:
        stats: Cache statistics

    Returns:
        List of optimization recommendations
    """
    recommendations = []
    hit_rate = stats.get("hit_rate", 0)

    if hit_rate < 0.3:
        recommendations.append("Consider increasing cache TTL for better hit rates")
        recommendations.append("Review query patterns for optimization opportunities")

    if hit_rate > 0.8:
        recommendations.append("Excellent cache performance - consider expanding cache size")

    memory_usage = stats.get("used_memory", 0)
    if memory_usage > 1024 * 1024 * 100:  # 100MB
        recommendations.append("High memory usage - consider cache cleanup or size limits")

    if not recommendations:
        recommendations.append("Cache performance is within normal parameters")

    return recommendations


async def performance_metrics_resource(
    strategy: Optional[str] = None,
    time_range: str = "1h"
) -> Dict[str, Any]:
    """Get performance metrics for retrieval strategies.

    URI Pattern: metrics://{strategy}?time_range={time_range}

    Args:
        strategy: Specific strategy to analyze (optional)
        time_range: Time range for metrics (1h, 24h, 7d)

    Returns:
        Performance metrics and trends
    """
    try:
        # In a production system, this would query actual metrics storage
        # For now, return mock data structure

        if strategy:
            return {
                "strategy": strategy,
                "time_range": time_range,
                "metrics": {
                    "avg_latency_ms": 85.2,
                    "p95_latency_ms": 150.0,
                    "success_rate": 0.98,
                    "total_requests": 1547,
                    "avg_results_count": 4.2,
                    "cache_hit_rate": 0.72
                },
                "trends": {
                    "latency_trend": "stable",
                    "success_rate_trend": "improving",
                    "usage_trend": "increasing"
                },
                "resource_type": "performance_metrics",
                "timestamp": time.time()
            }

        else:
            return {
                "time_range": time_range,
                "all_strategies": {
                    "bm25": {"avg_latency_ms": 15.3, "success_rate": 0.99},
                    "vector": {"avg_latency_ms": 25.7, "success_rate": 0.97},
                    "ensemble": {"avg_latency_ms": 185.2, "success_rate": 0.95},
                    "rerank": {"avg_latency_ms": 220.1, "success_rate": 0.94}
                },
                "top_performers": ["bm25", "vector", "parent_doc"],
                "resource_type": "performance_metrics",
                "timestamp": time.time()
            }

    except Exception as e:
        return {
            "error": str(e),
            "strategy": strategy,
            "time_range": time_range,
            "resource_type": "performance_metrics",
            "timestamp": time.time()
        }