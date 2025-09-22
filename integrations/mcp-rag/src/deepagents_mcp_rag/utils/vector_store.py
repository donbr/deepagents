"""Qdrant vector store utilities."""

from typing import Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, CreateCollection
from ..config import get_settings
from .embeddings import get_embedding_dimension


# Global Qdrant client instance
_qdrant_client = None


async def get_qdrant_client() -> AsyncQdrantClient:
    """Get the global Qdrant client instance.

    Returns:
        AsyncQdrantClient instance
    """
    global _qdrant_client

    if _qdrant_client is None:
        settings = get_settings()

        # Initialize client with proper configuration
        if settings.qdrant_api_key:
            _qdrant_client = AsyncQdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                timeout=30.0
            )
        else:
            _qdrant_client = AsyncQdrantClient(
                url=settings.qdrant_url,
                timeout=30.0
            )

    return _qdrant_client


async def ensure_collection_exists(
    collection_name: str,
    vector_size: Optional[int] = None
) -> bool:
    """Ensure a Qdrant collection exists with proper configuration.

    Args:
        collection_name: Name of the collection
        vector_size: Vector dimension (defaults to embedding model dimension)

    Returns:
        True if collection exists or was created successfully
    """
    try:
        client = await get_qdrant_client()

        # Check if collection already exists
        collections = await client.get_collections()
        existing_collections = [col.name for col in collections.collections]

        if collection_name in existing_collections:
            return True

        # Create collection if it doesn't exist
        if vector_size is None:
            vector_size = get_embedding_dimension()

        await client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )

        return True

    except Exception as e:
        from .logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Failed to ensure collection {collection_name} exists: {e}")
        return False


async def get_collection_info(collection_name: str) -> dict:
    """Get information about a Qdrant collection.

    Args:
        collection_name: Name of the collection

    Returns:
        Dictionary with collection information
    """
    try:
        client = await get_qdrant_client()
        info = await client.get_collection(collection_name)

        return {
            "name": collection_name,
            "vectors_count": info.vectors_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "points_count": info.points_count,
            "status": info.status,
            "optimizer_status": info.optimizer_status,
            "disk_data_size": getattr(info, "disk_data_size", None),
            "ram_data_size": getattr(info, "ram_data_size", None),
        }

    except Exception as e:
        return {"error": f"Failed to get collection info: {e}"}


async def delete_collection(collection_name: str) -> bool:
    """Delete a Qdrant collection.

    Args:
        collection_name: Name of the collection to delete

    Returns:
        True if deleted successfully
    """
    try:
        client = await get_qdrant_client()
        await client.delete_collection(collection_name)
        return True

    except Exception as e:
        from .logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Failed to delete collection {collection_name}: {e}")
        return False


async def list_collections() -> list[str]:
    """List all Qdrant collections.

    Returns:
        List of collection names
    """
    try:
        client = await get_qdrant_client()
        collections = await client.get_collections()
        return [col.name for col in collections.collections]

    except Exception as e:
        from .logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Failed to list collections: {e}")
        return []