"""Embeddings utilities for vector operations."""

from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_community.embeddings import SentenceTransformerEmbeddings
from ..config import get_settings


class CachedEmbeddings:
    """Wrapper for embeddings with caching support."""

    def __init__(self, base_embeddings: Embeddings):
        self.base_embeddings = base_embeddings
        self._cache = {}

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents with caching."""
        # Check cache for each text
        cached_results = []
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            text_hash = hash(text)
            if text_hash in self._cache:
                cached_results.append((i, self._cache[text_hash]))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Embed uncached texts
        if uncached_texts:
            new_embeddings = await self.base_embeddings.aembed_documents(uncached_texts)

            # Cache new embeddings
            for text, embedding, idx in zip(uncached_texts, new_embeddings, uncached_indices):
                text_hash = hash(text)
                self._cache[text_hash] = embedding
                cached_results.append((idx, embedding))

        # Sort by original index and return embeddings
        cached_results.sort(key=lambda x: x[0])
        return [embedding for _, embedding in cached_results]

    async def aembed_query(self, text: str) -> list[float]:
        """Embed a single query with caching."""
        text_hash = hash(text)
        if text_hash in self._cache:
            return self._cache[text_hash]

        embedding = await self.base_embeddings.aembed_query(text)
        self._cache[text_hash] = embedding
        return embedding

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Synchronous embed multiple documents."""
        return self.base_embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        """Synchronous embed single query."""
        return self.base_embeddings.embed_query(text)


# Global embeddings instance
_embeddings = None


def get_embeddings() -> Embeddings:
    """Get the global embeddings instance.

    Returns:
        Embeddings instance for vector operations
    """
    global _embeddings

    if _embeddings is None:
        settings = get_settings()

        # Initialize embeddings based on model name
        if settings.embed_model.startswith("sentence-transformers/"):
            model_name = settings.embed_model.replace("sentence-transformers/", "")
            base_embeddings = SentenceTransformerEmbeddings(
                model_name=model_name,
                cache_folder=None,  # Use default cache
            )
        else:
            # Default to all-MiniLM-L6-v2 for unknown models
            base_embeddings = SentenceTransformerEmbeddings(
                model_name="all-MiniLM-L6-v2"
            )

        # Wrap with caching
        _embeddings = CachedEmbeddings(base_embeddings)

    return _embeddings


def get_embedding_dimension() -> int:
    """Get the embedding dimension for the current model.

    Returns:
        Embedding vector dimension
    """
    settings = get_settings()

    # Common embedding dimensions
    dimension_map = {
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
        "multi-qa-MiniLM-L6-cos-v1": 384,
        "paraphrase-multilingual-MiniLM-L12-v2": 384,
    }

    model_name = settings.embed_model.replace("sentence-transformers/", "")
    return dimension_map.get(model_name, 384)  # Default to 384