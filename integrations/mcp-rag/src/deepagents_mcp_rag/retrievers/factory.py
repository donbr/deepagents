"""Factory pattern for creating retrieval strategies."""

from typing import Dict, Type, Any, Optional
from .base import BaseRetriever


class RetrieverFactory:
    """Factory for creating retrieval strategy instances.

    Provides a centralized way to instantiate different retrieval strategies
    with consistent configuration and strategy selection logic.
    """

    _strategies: Dict[str, Type[BaseRetriever]] = {}

    @classmethod
    def register_strategy(cls, name: str, strategy_class: Type[BaseRetriever]) -> None:
        """Register a new retrieval strategy.

        Args:
            name: Strategy name identifier
            strategy_class: Retriever class implementing BaseRetriever
        """
        cls._strategies[name] = strategy_class

    @classmethod
    def create(cls, strategy: str, **kwargs) -> BaseRetriever:
        """Create a retriever instance for the specified strategy.

        Args:
            strategy: Strategy name ('bm25', 'vector', 'parent_doc', etc.)
            **kwargs: Strategy-specific configuration parameters

        Returns:
            Configured retriever instance

        Raises:
            ValueError: If strategy is not recognized
        """
        # Handle auto strategy selection
        if strategy == "auto":
            strategy = cls._select_auto_strategy(kwargs.get("query", ""))

        # Lazy import to avoid circular dependencies
        if not cls._strategies:
            cls._register_builtin_strategies()

        if strategy not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(
                f"Unknown retrieval strategy: {strategy}. "
                f"Available strategies: {available}"
            )

        strategy_class = cls._strategies[strategy]
        return strategy_class(**kwargs)

    @classmethod
    def list_strategies(cls) -> Dict[str, Dict[str, Any]]:
        """List all available retrieval strategies with descriptions.

        Returns:
            Dictionary mapping strategy names to their information
        """
        if not cls._strategies:
            cls._register_builtin_strategies()

        strategies = {}
        for name, strategy_class in cls._strategies.items():
            # Create temporary instance to get info
            try:
                temp_instance = strategy_class(k=1)
                info = temp_instance.get_info()
                info.update({
                    "class": strategy_class.__name__,
                    "description": strategy_class.__doc__ or "No description available",
                })
                strategies[name] = info
            except Exception:
                strategies[name] = {
                    "class": strategy_class.__name__,
                    "description": "Error getting strategy info",
                    "error": True,
                }

        return strategies

    @classmethod
    def _register_builtin_strategies(cls) -> None:
        """Register all built-in retrieval strategies."""
        from .bm25 import BM25Retriever
        from .vector import VectorRetriever
        from .parent_doc import ParentDocRetriever
        from .multi_query import MultiQueryRetriever
        from .rerank import RerankRetriever
        from .ensemble import EnsembleRetriever

        strategies = {
            "bm25": BM25Retriever,
            "vector": VectorRetriever,
            "parent_doc": ParentDocRetriever,
            "multi_query": MultiQueryRetriever,
            "rerank": RerankRetriever,
            "ensemble": EnsembleRetriever,
        }

        for name, strategy_class in strategies.items():
            cls.register_strategy(name, strategy_class)

    @classmethod
    def _select_auto_strategy(cls, query: str) -> str:
        """Automatically select optimal strategy based on query characteristics.

        Args:
            query: Search query to analyze

        Returns:
            Selected strategy name
        """
        # Simple heuristics for strategy selection
        # In production, this could use ML models or more sophisticated analysis

        query_lower = query.lower()
        query_length = len(query.split())

        # Short, specific queries - use BM25 for exact matching
        if query_length <= 3 and any(
            keyword in query_lower for keyword in ["what", "when", "where", "who"]
        ):
            return "bm25"

        # Technical queries with specific terms - use BM25
        if any(tech_term in query_lower for tech_term in [
            "function", "class", "method", "api", "error", "bug", "fix"
        ]):
            return "bm25"

        # Complex conceptual queries - use ensemble for best coverage
        if query_length > 10 or any(
            keyword in query_lower for keyword in ["explain", "how", "why", "compare"]
        ):
            return "ensemble"

        # Medium complexity - use vector search for semantic understanding
        if 4 <= query_length <= 10:
            return "vector"

        # Default to ensemble for unknown cases
        return "ensemble"

    @classmethod
    def get_strategy_recommendations(cls, query: str) -> Dict[str, Any]:
        """Get strategy recommendations with reasoning for a query.

        Args:
            query: Search query to analyze

        Returns:
            Dictionary with recommended strategies and reasoning
        """
        auto_strategy = cls._select_auto_strategy(query)
        query_length = len(query.split())

        recommendations = {
            "primary": auto_strategy,
            "alternatives": [],
            "reasoning": "",
            "query_analysis": {
                "length": query_length,
                "type": "unknown",
            }
        }

        # Analyze query type
        query_lower = query.lower()

        if any(keyword in query_lower for keyword in ["what", "when", "where", "who"]):
            recommendations["query_analysis"]["type"] = "factual"
            recommendations["reasoning"] = "Factual question detected - BM25 for exact matching"
            recommendations["alternatives"] = ["vector", "rerank"]

        elif any(keyword in query_lower for keyword in ["how", "why", "explain"]):
            recommendations["query_analysis"]["type"] = "conceptual"
            recommendations["reasoning"] = "Conceptual question - ensemble for comprehensive coverage"
            recommendations["alternatives"] = ["multi_query", "vector"]

        elif any(tech_term in query_lower for tech_term in [
            "function", "class", "method", "api", "error", "bug"
        ]):
            recommendations["query_analysis"]["type"] = "technical"
            recommendations["reasoning"] = "Technical query - BM25 for precise term matching"
            recommendations["alternatives"] = ["parent_doc", "rerank"]

        else:
            recommendations["query_analysis"]["type"] = "general"
            recommendations["reasoning"] = "General query - vector search for semantic understanding"
            recommendations["alternatives"] = ["ensemble", "rerank"]

        return recommendations


# Register factory as a convenience function
def create_retriever(strategy: str, **kwargs) -> BaseRetriever:
    """Convenience function to create a retriever.

    Args:
        strategy: Strategy name
        **kwargs: Strategy configuration

    Returns:
        Configured retriever instance
    """
    return RetrieverFactory.create(strategy, **kwargs)