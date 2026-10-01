"""
Caching package for Phase 4.
Provides in-memory LRU with TTL and Redis compatibility layer for high-throughput concurrency.
"""

from core.cache.cache_manager import CacheManager, cached, GLOBAL_CACHE

__all__ = ["CacheManager", "cached", "GLOBAL_CACHE"]
