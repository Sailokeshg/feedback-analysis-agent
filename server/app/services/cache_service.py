"""
Redis caching service for analytics endpoints.
Provides fast access to computed analytics data with TTL-based expiration.
"""

import json
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import redis

from ..config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service for analytics data."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis connection."""
        self.redis_url = redis_url or settings.external.redis_url
        self.redis_client = None

        if self.redis_url:
            try:
                self.redis_client = redis.from_url(self.redis_url)
                # Test connection
                self.redis_client.ping()
                logger.info("Connected to Redis for caching")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
                self.redis_client = None

    def _make_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate a cache key from prefix and parameters."""
        # Sort params for consistent key generation
        param_str = json.dumps(params, sort_keys=True, default=str)
        return f"analytics:{prefix}:{hash(param_str)}"

    def get(self, prefix: str, params: Dict[str, Any]) -> Optional[Any]:
        """Get cached data if available and not expired."""
        if not self.redis_client:
            return None

        key = self._make_key(prefix, params)
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(cached_data.decode('utf-8'))
        except Exception as e:
            logger.warning(f"Cache get error: {e}")

        logger.debug(f"Cache miss for key: {key}")
        return None

    def set(self, prefix: str, params: Dict[str, Any], data: Any, ttl_seconds: int = 300) -> bool:
        """Cache data with TTL (default 5 minutes)."""
        if not self.redis_client:
            return False

        key = self._make_key(prefix, params)
        try:
            serialized_data = json.dumps(data, default=str)
            self.redis_client.setex(key, ttl_seconds, serialized_data)
            logger.debug(f"Cached data for key: {key} with TTL {ttl_seconds}s")
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern."""
        if not self.redis_client:
            return 0

        try:
            # Use SCAN to find keys matching the pattern
            keys_to_delete = []
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, match=pattern, count=100)
                keys_to_delete.extend(keys)
                if cursor == 0:
                    break

            if keys_to_delete:
                deleted_count = self.redis_client.delete(*keys_to_delete)
                logger.info(f"Invalidated {deleted_count} cache keys matching pattern: {pattern}")
                return deleted_count
            else:
                logger.debug(f"No cache keys found matching pattern: {pattern}")
                return 0
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
            return 0

    def invalidate_analytics_cache(self) -> int:
        """Invalidate all analytics cache keys."""
        return self.invalidate_pattern("analytics:*")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache statistics and info."""
        if not self.redis_client:
            return {"status": "disabled", "reason": "no redis connection"}

        try:
            info = self.redis_client.info()
            keys_count = len(self.redis_client.keys("analytics:*"))
            return {
                "status": "connected",
                "keys_count": keys_count,
                "memory_used": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Global cache service instance
cache_service = CacheService()
