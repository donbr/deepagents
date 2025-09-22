"""Redis-based caching utilities for retrieval optimization."""

import os
import json
import pickle
from typing import Any, Optional
import redis.asyncio as redis
from ..config import get_settings


class CacheClient:
    """Async Redis cache client for retrieval results."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client = None

    async def _get_client(self):
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(self.redis_url)
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            client = await self._get_client()
            value = await client.get(key)

            if value is not None:
                # Try to deserialize as pickle first, then JSON
                try:
                    return pickle.loads(value)
                except (pickle.PickleError, TypeError):
                    try:
                        return json.loads(value.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        return value.decode()

            return None

        except Exception:
            # Fail silently for cache errors
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()

            # Serialize value
            if isinstance(value, (str, bytes)):
                serialized = value
            else:
                try:
                    # Try pickle for complex objects
                    serialized = pickle.dumps(value)
                except (pickle.PickleError, TypeError):
                    # Fallback to JSON
                    serialized = json.dumps(value, default=str)

            await client.setex(key, ttl, serialized)
            return True

        except Exception:
            # Fail silently for cache errors
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            await client.delete(key)
            return True

        except Exception:
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern.

        Args:
            pattern: Redis pattern (e.g., "retrieval:*")

        Returns:
            Number of keys deleted
        """
        try:
            client = await self._get_client()
            keys = await client.keys(pattern)
            if keys:
                await client.delete(*keys)
                return len(keys)
            return 0

        except Exception:
            return 0

    async def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            client = await self._get_client()
            info = await client.info("stats")

            return {
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": info.get("keyspace_hits", 0) / max(
                    info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1
                ),
                "total_commands": info.get("total_commands_processed", 0),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
            }

        except Exception:
            return {"error": "Failed to get cache stats"}

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()


# Global cache client instance
_cache_client = None


async def get_cache_client() -> CacheClient:
    """Get the global cache client instance.

    Returns:
        CacheClient instance
    """
    global _cache_client

    if _cache_client is None:
        settings = get_settings()
        _cache_client = CacheClient(settings.redis_url)

    return _cache_client


async def clear_retrieval_cache() -> int:
    """Clear all retrieval-related cache entries.

    Returns:
        Number of cache entries cleared
    """
    cache = await get_cache_client()
    return await cache.clear_pattern("retrieval:*")