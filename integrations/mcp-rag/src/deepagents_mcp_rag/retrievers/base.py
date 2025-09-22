"""Base retriever interface for all retrieval strategies."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain_core.documents import Document


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval performance tracking."""

    strategy: str
    query: str
    num_results: int
    latency_ms: float
    token_count: Optional[int] = None
    cache_hit: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging."""
        return {
            "strategy": self.strategy,
            "query": self.query,
            "num_results": self.num_results,
            "latency_ms": self.latency_ms,
            "token_count": self.token_count,
            "cache_hit": self.cache_hit,
        }


class BaseRetriever(ABC):
    """Abstract base class for all retrieval strategies.

    Provides common interface and functionality for different retrieval
    approaches including timing, caching, and error handling.
    """

    def __init__(
        self,
        k: int = 5,
        enable_caching: bool = True,
        cache_ttl: int = 3600,
        **kwargs
    ):
        """Initialize base retriever.

        Args:
            k: Number of documents to retrieve
            enable_caching: Whether to enable result caching
            cache_ttl: Cache time-to-live in seconds
            **kwargs: Strategy-specific configuration
        """
        self.k = k
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl
        self.strategy_name = self.__class__.__name__.replace("Retriever", "").lower()

    @abstractmethod
    async def _retrieve_impl(self, query: str, **kwargs) -> List[Document]:
        """Implementation of retrieval strategy.

        Args:
            query: Search query
            **kwargs: Strategy-specific parameters

        Returns:
            List of retrieved documents
        """
        pass

    async def retrieve(self, query: str, **kwargs) -> List[Document]:
        """Retrieve documents with metrics tracking and caching.

        Args:
            query: Search query
            **kwargs: Strategy-specific parameters

        Returns:
            List of retrieved documents with metadata
        """
        import time
        from ..utils.cache import get_cache_client
        from ..utils.logging import get_logger

        logger = get_logger(__name__)
        start_time = time.time()

        # Check cache if enabled
        cache_key = None
        if self.enable_caching:
            cache_client = get_cache_client()
            cache_key = f"retrieval:{self.strategy_name}:{hash(query)}:{self.k}"

            try:
                cached_result = await cache_client.get(cache_key)
                if cached_result:
                    latency_ms = (time.time() - start_time) * 1000
                    logger.info(f"Cache hit for {self.strategy_name} retrieval")

                    # Log metrics
                    metrics = RetrievalMetrics(
                        strategy=self.strategy_name,
                        query=query,
                        num_results=len(cached_result),
                        latency_ms=latency_ms,
                        cache_hit=True
                    )
                    await self._log_metrics(metrics)

                    return cached_result
            except Exception as e:
                logger.warning(f"Cache error: {e}")

        try:
            # Execute retrieval
            documents = await self._retrieve_impl(query, **kwargs)

            # Ensure we don't exceed k limit
            if len(documents) > self.k:
                documents = documents[:self.k]

            # Cache result if enabled
            if self.enable_caching and cache_key:
                try:
                    cache_client = get_cache_client()
                    await cache_client.set(cache_key, documents, ttl=self.cache_ttl)
                except Exception as e:
                    logger.warning(f"Cache write error: {e}")

            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000

            # Count tokens if possible
            token_count = None
            try:
                token_count = sum(len(doc.page_content.split()) for doc in documents)
            except Exception:
                pass

            metrics = RetrievalMetrics(
                strategy=self.strategy_name,
                query=query,
                num_results=len(documents),
                latency_ms=latency_ms,
                token_count=token_count,
                cache_hit=False
            )

            await self._log_metrics(metrics)

            logger.info(
                f"{self.strategy_name} retrieval completed: "
                f"{len(documents)} docs in {latency_ms:.2f}ms"
            )

            return documents

        except Exception as e:
            logger.error(f"{self.strategy_name} retrieval failed: {e}")
            raise

    async def _log_metrics(self, metrics: RetrievalMetrics) -> None:
        """Log retrieval metrics for observability.

        Args:
            metrics: Retrieval metrics to log
        """
        from ..utils.telemetry import log_retrieval_metrics

        try:
            await log_retrieval_metrics(metrics)
        except Exception as e:
            # Don't fail retrieval due to metrics logging issues
            pass

    def get_info(self) -> Dict[str, Any]:
        """Get information about this retriever strategy.

        Returns:
            Dictionary with strategy information
        """
        return {
            "strategy": self.strategy_name,
            "k": self.k,
            "enable_caching": self.enable_caching,
            "cache_ttl": self.cache_ttl,
        }