"""Ensemble retrieval strategy using Reciprocal Rank Fusion.

Combines multiple retrieval strategies using RRF algorithm to achieve
optimal performance across diverse query types.
"""

from typing import List, Dict, Any, Optional, Set
from collections import defaultdict
from langchain_core.documents import Document

from .base import BaseRetriever


class EnsembleRetriever(BaseRetriever):
    """Ensemble retrieval using Reciprocal Rank Fusion (RRF).

    Combines results from multiple retrieval strategies using RRF algorithm
    to achieve optimal F1 score across diverse query types. Excellent for:
    - General-purpose retrieval with consistent performance
    - Unknown query types requiring robust performance
    - Production systems needing reliable results

    Performance characteristics:
    - Latency: ~180ms (parallel execution of multiple strategies)
    - Best for: Overall F1 score, consistent performance
    - Weakness: Higher computational cost
    """

    def __init__(
        self,
        k: int = 5,
        strategies: Optional[List[str]] = None,
        strategy_weights: Optional[Dict[str, float]] = None,
        rrf_constant: int = 60,
        enable_parallel: bool = True,
        collection_name: str = "deepagents_documents",
        **kwargs
    ):
        """Initialize ensemble retriever.

        Args:
            k: Number of documents to return
            strategies: List of strategies to combine (default: ["bm25", "vector", "rerank"])
            strategy_weights: Weights for each strategy in fusion
            rrf_constant: RRF constant (default 60, higher = less aggressive)
            enable_parallel: Whether to run strategies in parallel
            collection_name: Vector store collection name
            **kwargs: Base retriever arguments
        """
        super().__init__(k=k, **kwargs)

        # Default to proven high-performance combination
        self.strategies = strategies or ["bm25", "vector", "rerank"]
        self.strategy_weights = strategy_weights or {}
        self.rrf_constant = rrf_constant
        self.enable_parallel = enable_parallel
        self.collection_name = collection_name

        self._retrievers = {}
        self._initialized = False

    async def _retrieve_impl(self, query: str, **kwargs) -> List[Document]:
        """Implement ensemble retrieval with RRF fusion.

        Args:
            query: Search query
            **kwargs: Additional parameters

        Returns:
            List of documents ranked by RRF fusion score
        """
        # Ensure retrievers are initialized
        await self._ensure_retrievers_initialized()

        if not self._retrievers:
            return []

        try:
            # Step 1: Retrieve from all strategies
            if self.enable_parallel:
                strategy_results = await self._retrieve_parallel(query)
            else:
                strategy_results = await self._retrieve_sequential(query)

            # Step 2: Apply RRF fusion
            fused_results = self._apply_rrf_fusion(strategy_results)

            # Step 3: Add ensemble metadata
            final_docs = []
            for i, (doc, score) in enumerate(fused_results[:self.k]):
                doc.metadata = doc.metadata.copy()
                doc.metadata.update({
                    "retrieval_strategy": "ensemble",
                    "ensemble_strategies": self.strategies,
                    "rank": i + 1,
                    "rrf_score": float(score),
                    "contributing_strategies": self._get_contributing_strategies(doc, strategy_results)
                })
                final_docs.append(doc)

            return final_docs

        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Ensemble retrieval failed: {e}")
            return []

    async def _retrieve_parallel(self, query: str) -> Dict[str, List[Document]]:
        """Retrieve from all strategies in parallel.

        Args:
            query: Search query

        Returns:
            Dictionary mapping strategy names to retrieved documents
        """
        import asyncio

        # Create retrieval tasks
        tasks = {}
        for strategy in self.strategies:
            if strategy in self._retrievers:
                tasks[strategy] = self._retrievers[strategy].retrieve(query)

        # Execute in parallel
        if not tasks:
            return {}

        try:
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)

            # Combine results with strategy names
            strategy_results = {}
            for strategy, result in zip(tasks.keys(), results):
                if isinstance(result, Exception):
                    from ..utils.logging import get_logger
                    logger = get_logger(__name__)
                    logger.error(f"Strategy {strategy} failed: {result}")
                    strategy_results[strategy] = []
                else:
                    strategy_results[strategy] = result or []

            return strategy_results

        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Parallel retrieval failed: {e}")
            return {}

    async def _retrieve_sequential(self, query: str) -> Dict[str, List[Document]]:
        """Retrieve from all strategies sequentially.

        Args:
            query: Search query

        Returns:
            Dictionary mapping strategy names to retrieved documents
        """
        strategy_results = {}

        for strategy in self.strategies:
            if strategy in self._retrievers:
                try:
                    results = await self._retrievers[strategy].retrieve(query)
                    strategy_results[strategy] = results or []
                except Exception as e:
                    from ..utils.logging import get_logger
                    logger = get_logger(__name__)
                    logger.error(f"Strategy {strategy} failed: {e}")
                    strategy_results[strategy] = []

        return strategy_results

    def _apply_rrf_fusion(
        self,
        strategy_results: Dict[str, List[Document]]
    ) -> List[tuple[Document, float]]:
        """Apply Reciprocal Rank Fusion to combine strategy results.

        Args:
            strategy_results: Results from each strategy

        Returns:
            List of (document, rrf_score) tuples sorted by score
        """
        # Document scores accumulator
        doc_scores = defaultdict(float)
        doc_objects = {}  # Keep track of document objects

        # Apply RRF formula: score = sum(1 / (rank + constant))
        for strategy, docs in strategy_results.items():
            weight = self.strategy_weights.get(strategy, 1.0)

            for rank, doc in enumerate(docs):
                # Use content hash as document identifier for deduplication
                doc_id = self._get_document_id(doc)

                # RRF score calculation
                rrf_score = weight / (rank + 1 + self.rrf_constant)
                doc_scores[doc_id] += rrf_score

                # Keep the document object (preferring one with more metadata)
                if doc_id not in doc_objects or len(doc.metadata) > len(doc_objects[doc_id].metadata):
                    doc_objects[doc_id] = doc

        # Sort by RRF score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Return documents with scores
        return [(doc_objects[doc_id], score) for doc_id, score in sorted_docs]

    def _get_document_id(self, doc: Document) -> str:
        """Get a unique identifier for a document for deduplication.

        Args:
            doc: Document to identify

        Returns:
            Unique document identifier
        """
        # Use combination of content hash and source for identification
        content_hash = hash(doc.page_content[:1000])  # Use first 1000 chars
        source = doc.metadata.get("source", "unknown")
        return f"{source}:{content_hash}"

    def _get_contributing_strategies(
        self,
        doc: Document,
        strategy_results: Dict[str, List[Document]]
    ) -> List[str]:
        """Get list of strategies that contributed this document.

        Args:
            doc: Document to check
            strategy_results: Results from all strategies

        Returns:
            List of strategy names that retrieved this document
        """
        doc_id = self._get_document_id(doc)
        contributing = []

        for strategy, docs in strategy_results.items():
            for strategy_doc in docs:
                if self._get_document_id(strategy_doc) == doc_id:
                    contributing.append(strategy)
                    break

        return contributing

    async def _ensure_retrievers_initialized(self) -> None:
        """Ensure all strategy retrievers are initialized."""
        if self._initialized:
            return

        try:
            from .factory import RetrieverFactory

            # Initialize retrievers for each strategy
            for strategy in self.strategies:
                try:
                    # Use larger k for individual strategies to get more candidates
                    strategy_k = min(self.k * 3, 15)  # 3x our target, max 15

                    retriever = RetrieverFactory.create(
                        strategy,
                        k=strategy_k,
                        collection_name=self.collection_name,
                        enable_caching=self.enable_caching
                    )
                    self._retrievers[strategy] = retriever

                except Exception as e:
                    from ..utils.logging import get_logger
                    logger = get_logger(__name__)
                    logger.error(f"Failed to initialize {strategy} retriever: {e}")

            self._initialized = True

        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to initialize ensemble retrievers: {e}")

    def get_info(self) -> Dict[str, Any]:
        """Get ensemble retriever information."""
        info = super().get_info()

        # Get info from individual retrievers
        strategy_info = {}
        for strategy, retriever in self._retrievers.items():
            try:
                strategy_info[strategy] = retriever.get_info()
            except Exception:
                strategy_info[strategy] = {"error": "Failed to get info"}

        info.update({
            "algorithm": "Reciprocal Rank Fusion (RRF)",
            "strategies": self.strategies,
            "strategy_weights": self.strategy_weights,
            "rrf_constant": self.rrf_constant,
            "enable_parallel": self.enable_parallel,
            "collection_name": self.collection_name,
            "best_for": ["general_purpose", "consistent_performance", "unknown_query_types"],
            "characteristics": {
                "latency": "~180ms",
                "accuracy": "optimal_f1_score",
                "consistency": "excellent"
            },
            "initialized_strategies": list(self._retrievers.keys()),
            "strategy_details": strategy_info
        })
        return info

    async def get_strategy_breakdown(self, query: str) -> Dict[str, Any]:
        """Get detailed breakdown of how each strategy contributed.

        Args:
            query: Search query to analyze

        Returns:
            Detailed breakdown of ensemble performance
        """
        await self._ensure_retrievers_initialized()

        if not self._retrievers:
            return {"error": "No retrievers initialized"}

        try:
            # Get results from each strategy
            if self.enable_parallel:
                strategy_results = await self._retrieve_parallel(query)
            else:
                strategy_results = await self._retrieve_sequential(query)

            # Analyze contribution of each strategy
            analysis = {
                "query": query,
                "strategies_used": list(strategy_results.keys()),
                "strategy_results": {},
                "fusion_analysis": {}
            }

            # Analyze each strategy's results
            for strategy, docs in strategy_results.items():
                analysis["strategy_results"][strategy] = {
                    "num_docs": len(docs),
                    "top_3_snippets": [
                        doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                        for doc in docs[:3]
                    ]
                }

            # Analyze fusion
            fused_results = self._apply_rrf_fusion(strategy_results)
            analysis["fusion_analysis"] = {
                "total_unique_docs": len(fused_results),
                "top_k_sources": [
                    {
                        "rank": i + 1,
                        "rrf_score": score,
                        "contributing_strategies": self._get_contributing_strategies(doc, strategy_results),
                        "snippet": doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                    }
                    for i, (doc, score) in enumerate(fused_results[:self.k])
                ]
            }

            return analysis

        except Exception as e:
            return {"error": f"Failed to generate strategy breakdown: {e}"}

    def update_strategy_weights(self, weights: Dict[str, float]) -> None:
        """Update strategy weights for fusion.

        Args:
            weights: New weights for each strategy
        """
        self.strategy_weights.update(weights)

    def add_strategy(self, strategy: str, weight: float = 1.0) -> None:
        """Add a new strategy to the ensemble.

        Args:
            strategy: Strategy name to add
            weight: Weight for the new strategy
        """
        if strategy not in self.strategies:
            self.strategies.append(strategy)
            self.strategy_weights[strategy] = weight
            # Force reinitialization
            self._initialized = False

    def remove_strategy(self, strategy: str) -> None:
        """Remove a strategy from the ensemble.

        Args:
            strategy: Strategy name to remove
        """
        if strategy in self.strategies:
            self.strategies.remove(strategy)
            self.strategy_weights.pop(strategy, None)
            self._retrievers.pop(strategy, None)