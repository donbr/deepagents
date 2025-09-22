"""Vector similarity retrieval strategy using dense embeddings.

Implements semantic search using vector embeddings for contextual
understanding beyond keyword matching.
"""

from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langchain_core.embeddings import Embeddings

from .base import BaseRetriever


class VectorRetriever(BaseRetriever):
    """Vector similarity retrieval using dense embeddings.

    Uses sentence embeddings to find semantically similar documents
    based on vector similarity (cosine distance). Excellent for:
    - Conceptual questions requiring semantic understanding
    - Finding related content with different wording
    - Cross-lingual retrieval (with multilingual embeddings)

    Performance characteristics:
    - Latency: ~20ms for 1M vectors (approximate search)
    - Best for: Semantic similarity, conceptual queries
    - Weakness: May miss exact term matches
    """

    def __init__(
        self,
        k: int = 5,
        collection_name: str = "deepagents_documents",
        similarity_threshold: float = 0.0,
        **kwargs
    ):
        """Initialize vector retriever.

        Args:
            k: Number of documents to retrieve
            collection_name: Qdrant collection name
            similarity_threshold: Minimum similarity score (0.0-1.0)
            **kwargs: Base retriever arguments
        """
        super().__init__(k=k, **kwargs)
        self.collection_name = collection_name
        self.similarity_threshold = similarity_threshold
        self._vector_store = None
        self._embeddings = None

    async def _retrieve_impl(self, query: str, **kwargs) -> List[Document]:
        """Implement vector similarity retrieval.

        Args:
            query: Search query
            **kwargs: Additional parameters (similarity_threshold, etc.)

        Returns:
            List of documents ranked by similarity score
        """
        # Ensure vector store is initialized
        await self._ensure_vector_store()

        if not self._vector_store:
            return []

        # Override similarity threshold if provided
        threshold = kwargs.get("similarity_threshold", self.similarity_threshold)

        try:
            # Perform similarity search with scores
            results = await self._vector_store.asimilarity_search_with_score(
                query=query,
                k=self.k
            )

            # Filter by similarity threshold and add metadata
            filtered_results = []
            for doc, score in results:
                if score >= threshold:
                    # Add vector search metadata
                    doc.metadata = doc.metadata.copy()
                    doc.metadata.update({
                        "similarity_score": float(score),
                        "retrieval_strategy": "vector",
                        "rank": len(filtered_results) + 1,
                        "collection": self.collection_name
                    })
                    filtered_results.append(doc)

            return filtered_results

        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Vector retrieval failed: {e}")
            return []

    async def _ensure_vector_store(self) -> None:
        """Ensure vector store connection is established."""
        if self._vector_store is not None:
            return

        try:
            from ..utils.embeddings import get_embeddings
            from ..utils.vector_store import get_qdrant_client

            # Get embeddings model
            self._embeddings = get_embeddings()

            # Get Qdrant client
            qdrant_client = get_qdrant_client()

            # Initialize vector store
            self._vector_store = QdrantVectorStore(
                client=qdrant_client,
                collection_name=self.collection_name,
                embeddings=self._embeddings
            )

        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to initialize vector store: {e}")
            self._vector_store = None

    def get_info(self) -> Dict[str, Any]:
        """Get vector retriever information."""
        info = super().get_info()
        info.update({
            "algorithm": "Dense Vector Similarity",
            "embedding_model": getattr(self._embeddings, "model_name", "unknown"),
            "collection_name": self.collection_name,
            "similarity_threshold": self.similarity_threshold,
            "best_for": ["semantic_search", "conceptual_queries", "cross_lingual"],
            "characteristics": {
                "latency": "~20ms",
                "accuracy": "high_for_semantic_similarity",
                "semantic_understanding": "excellent"
            },
            "vector_store_connected": self._vector_store is not None
        })
        return info

    async def similarity_search_with_score_threshold(
        self,
        query: str,
        score_threshold: float,
        k: Optional[int] = None
    ) -> List[Document]:
        """Search with a specific similarity score threshold.

        Args:
            query: Search query
            score_threshold: Minimum similarity score
            k: Number of results (defaults to self.k)

        Returns:
            Documents above the similarity threshold
        """
        original_k = self.k
        original_threshold = self.similarity_threshold

        try:
            # Temporarily override settings
            if k is not None:
                self.k = k
            self.similarity_threshold = score_threshold

            return await self._retrieve_impl(query)

        finally:
            # Restore original settings
            self.k = original_k
            self.similarity_threshold = original_threshold

    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store.

        Args:
            documents: Documents to add
        """
        await self._ensure_vector_store()

        if self._vector_store:
            try:
                await self._vector_store.aadd_documents(documents)
            except Exception as e:
                from ..utils.logging import get_logger
                logger = get_logger(__name__)
                logger.error(f"Failed to add documents to vector store: {e}")

    async def delete_documents(self, ids: List[str]) -> None:
        """Delete documents from the vector store.

        Args:
            ids: Document IDs to delete
        """
        await self._ensure_vector_store()

        if self._vector_store:
            try:
                await self._vector_store.adelete(ids)
            except Exception as e:
                from ..utils.logging import get_logger
                logger = get_logger(__name__)
                logger.error(f"Failed to delete documents from vector store: {e}")

    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the vector collection.

        Returns:
            Collection metadata and statistics
        """
        await self._ensure_vector_store()

        if not self._vector_store:
            return {"error": "Vector store not available"}

        try:
            from ..utils.vector_store import get_qdrant_client

            client = get_qdrant_client()
            collection_info = await client.get_collection(self.collection_name)

            return {
                "collection_name": self.collection_name,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "points_count": collection_info.points_count,
                "status": collection_info.status,
                "optimizer_status": collection_info.optimizer_status,
            }

        except Exception as e:
            return {"error": f"Failed to get collection info: {e}"}