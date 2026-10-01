"""
Unit Tests for CacheManager, LRU Eviction, and Declarative Memoization Decorators.
"""

import time
import pytest
from core.cache import CacheManager, cached

def test_cache_set_and_get():
    cache = CacheManager(maxsize=10, default_ttl=5)
    cache.set("key1", "val1")
    assert cache.get("key1") == "val1"
    assert cache.get("non_existent") is None

def test_cache_ttl_expiration():
    cache = CacheManager(maxsize=10, default_ttl=1)
    cache.set("short_lived", "data", ttl_seconds=1)
    assert cache.get("short_lived") == "data"
    time.sleep(1.1)
    assert cache.get("short_lived") is None

def test_lru_eviction():
    cache = CacheManager(maxsize=3, default_ttl=60)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)

    # Access "a" so it is more recently used than "b"
    _ = cache.get("a")

    # Adding "d" should evict "b" (least recently used)
    cache.set("d", 4)
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3
    assert cache.get("d") == 4
    assert cache.evictions == 1

def test_cached_decorator():
    execution_counter = 0

    @cached(ttl_seconds=60, key_prefix="unit_test")
    def heavy_operation(n):
        nonlocal execution_counter
        execution_counter += 1
        return n * n

    res1 = heavy_operation(7)
    res2 = heavy_operation(7)
    assert res1 == 49
    assert res2 == 49
    assert execution_counter == 1
