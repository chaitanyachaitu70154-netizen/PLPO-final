"""
High-Performance Thread-Safe Caching System for Phase 4.
Implements:
1. Thread-safe LRU eviction with TTL (Time-To-Live).
2. Distributed Redis protocol support when REDIS_URL is configured.
3. Cache observability (hits, misses, evictions, latency).
4. Declarative caching decorators for expensive graph and LLM operations.
"""

import time
import os
import json
import logging
import functools
import threading
from typing import Any, Optional, Dict, Callable
from collections import OrderedDict

logger = logging.getLogger("plpo.cache")

class CacheItem:
    """Represents a cached payload with expiration metadata."""
    __slots__ = ("key", "value", "expires_at", "created_at")

    def __init__(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.expires_at = (self.created_at + ttl_seconds) if ttl_seconds else None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

class CacheManager:
    """
    Thread-safe in-memory LRU Cache with TTL support.
    Ready for distributed Redis clustering via REDIS_URL.
    """

    def __init__(self, maxsize: int = 1000, default_ttl: int = 300):
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheItem] = OrderedDict()
        self._lock = threading.RLock()

        # Telemetry metrics
        self.hits: int = 0
        self.misses: int = 0
        self.evictions: int = 0

        # Check for optional Redis connection
        self.redis_client = None
        self._init_redis_if_available()

    def _init_redis_if_available(self) -> None:
        redis_url = os.environ.get("REDIS_URL", "").strip()
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url, decode_responses=True, socket_timeout=2)
                self.redis_client.ping()
                logger.info(f"Connected to distributed Redis cache at {redis_url}")
            except Exception as e:
                logger.warning(f"Could not connect to Redis ({e}). Falling back to local in-memory LRU cache.")
                self.redis_client = None

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value by key, verifying TTL expiration."""
        # 1. Try Redis if enabled
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val is not None:
                    self.hits += 1
                    try:
                        return json.loads(val)
                    except Exception:
                        return val
                self.misses += 1
                return None
            except Exception as e:
                logger.debug(f"Redis get failed: {e}. Falling back to memory.")

        # 2. Local memory lookup
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None

            item = self._cache[key]
            if item.is_expired:
                del self._cache[key]
                self.misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self.hits += 1
            return item.value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store value with specified or default TTL."""
        effective_ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        # 1. Try Redis if enabled
        if self.redis_client:
            try:
                serialized = json.dumps(value) if not isinstance(value, (str, int, float, bool)) else str(value)
                self.redis_client.set(key, serialized, ex=effective_ttl)
                return
            except Exception as e:
                logger.debug(f"Redis set failed: {e}")

        # 2. Local memory storage
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self.maxsize:
                # Evict oldest (least recently used)
                oldest_key, _ = self._cache.popitem(last=False)
                self.evictions += 1
                logger.debug(f"Evicted LRU key: {oldest_key}")

            self._cache[key] = CacheItem(key, value, effective_ttl)

    def delete(self, key: str) -> None:
        """Remove key from cache."""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception:
                pass

        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self) -> None:
        """Clear all cached entries."""
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception:
                pass

        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0
            self.evictions = 0

    def get_stats(self) -> Dict[str, Any]:
        """Return cache health and telemetry statistics."""
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100.0) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "maxsize": self.maxsize,
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "hit_rate_pct": round(hit_rate, 1),
                "backend": "redis" if self.redis_client else "in_memory_lru"
            }

# Global singleton cache instance
GLOBAL_CACHE = CacheManager(maxsize=2000, default_ttl=300)

def cached(ttl_seconds: int = 300, key_prefix: str = ""):
    """
    Decorator for memoizing expensive function calls.
    Keys are generated from function name and serialized positional & keyword arguments.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Build deterministic cache key
            arg_str = "_".join(str(a) for a in args)
            kwarg_str = "_".join(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = f"{key_prefix}:{func.__name__}:{arg_str}:{kwarg_str}"

            cached_val = GLOBAL_CACHE.get(cache_key)
            if cached_val is not None:
                return cached_val

            result = func(*args, **kwargs)
            GLOBAL_CACHE.set(cache_key, result, ttl_seconds=ttl_seconds)
            return result
        return wrapper
    return decorator
