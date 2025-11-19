"""Redis caching service for performance optimization."""
import json
import logging
from typing import Optional, Any
import redis

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching frequently accessed data in Redis."""
    
    def __init__(self):
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache connected")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL."""
        if not self.redis_client:
            return False
        
        try:
            if ttl is None:
                ttl = settings.CACHE_EXPIRY
            
            serialized = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    def invalidate_articles_cache(self):
        """Invalidate all article-related caches."""
        self.delete_pattern("articles:*")
        self.delete("stats")
        logger.info("Invalidated article caches")


# Singleton instance
cache_service = CacheService()

