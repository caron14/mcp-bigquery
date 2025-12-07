"""Caching module for MCP BigQuery server."""

import hashlib
import json
import time
from typing import Any, Callable, Optional, Union

from .config import get_config
from .constants import CACHE_KEY_PREFIX
from .logging_config import get_logger

logger = get_logger(__name__)


class CacheEntry:
    """A cache entry with value and metadata."""

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() - self.created_at > self.ttl

    def access(self) -> Any:
        """Access the cache entry and update metadata."""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value


class Cache:
    """In-memory cache implementation."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of entries in cache
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "expirations": 0}

    def _make_key(self, prefix: str, *args: Any, **kwargs: Any) -> str:
        """
        Create a cache key from prefix and arguments.

        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        key_data = {"prefix": prefix, "args": args, "kwargs": sorted(kwargs.items())}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key in self._cache:
            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                logger.debug(f"Cache miss (expired): {key}")
                return None

            self._stats["hits"] += 1
            logger.debug(f"Cache hit: {key}")
            return entry.access()

        self._stats["misses"] += 1
        logger.debug(f"Cache miss: {key}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl

        # Check if we need to evict entries
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        self._cache[key] = CacheEntry(value, ttl)
        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache delete: {key}")
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find LRU entry
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)
        del self._cache[lru_key]
        self._stats["evictions"] += 1
        logger.debug(f"Cache eviction (LRU): {lru_key}")

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": hit_rate,
            "evictions": self._stats["evictions"],
            "expirations": self._stats["expirations"],
        }


class BigQueryClientCache:
    """Cache for BigQuery client instances."""

    def __init__(self):
        self._clients: dict[str, Any] = {}
        self._client_locks: dict[str, Any] = {}

    def get_client(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        builder: Optional[Callable[[Optional[str], Optional[str]], Any]] = None,
    ) -> Any:
        """
        Get or create a BigQuery client.

        Args:
            project_id: GCP project ID
            location: BigQuery location
            builder: Callable used to build a new client when cache misses

        Returns:
            BigQuery client instance
        """
        if builder is None:
            from .clients.factory import (
                _instantiate_client as builder,  # type: ignore[attr-defined]
            )

        key = f"{project_id or 'default'}:{location or 'default'}"

        if key not in self._clients:
            logger.info(f"Creating new BigQuery client for {key}")
            self._clients[key] = builder(project_id, location)
        else:
            logger.debug(f"Reusing BigQuery client for {key}")

        return self._clients[key]

    def clear(self) -> None:
        """Clear all cached clients."""
        self._clients.clear()
        logger.info("BigQuery client cache cleared")


# Global cache instances
_query_cache: Optional[Cache] = None
_schema_cache: Optional[Cache] = None
_client_cache: Optional[BigQueryClientCache] = None


def get_query_cache() -> Cache:
    """Get the global query cache instance."""
    global _query_cache
    if _query_cache is None:
        config = get_config()
        _query_cache = Cache(max_size=1000, default_ttl=config.cache_ttl)
    return _query_cache


def get_schema_cache() -> Cache:
    """Get the global schema cache instance."""
    global _schema_cache
    if _schema_cache is None:
        config = get_config()
        _schema_cache = Cache(
            max_size=500, default_ttl=config.cache_ttl * 2  # Schema changes less frequently
        )
    return _schema_cache


def get_client_cache() -> BigQueryClientCache:
    """Get the global BigQuery client cache instance."""
    global _client_cache
    if _client_cache is None:
        _client_cache = BigQueryClientCache()
    return _client_cache


def clear_all_caches() -> None:
    """Clear all cache instances."""
    if _query_cache:
        _query_cache.clear()
    if _schema_cache:
        _schema_cache.clear()
    if _client_cache:
        _client_cache.clear()
    logger.info("All caches cleared")


# Cache decorators
def cache_query_result(ttl: Optional[int] = None):
    """
    Decorator to cache query results.

    Args:
        ttl: Time-to-live in seconds
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            config = get_config()
            if not config.cache_enabled:
                return await func(*args, **kwargs)

            cache = get_query_cache()
            cache_key = cache._make_key(CACHE_KEY_PREFIX["query"], *args, **kwargs)

            # Check cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def cache_schema_info(ttl: Optional[int] = None):
    """
    Decorator to cache schema information.

    Args:
        ttl: Time-to-live in seconds
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            config = get_config()
            if not config.cache_enabled:
                return await func(*args, **kwargs)

            cache = get_schema_cache()
            cache_key = cache._make_key(CACHE_KEY_PREFIX["schema"], *args, **kwargs)

            # Check cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator
