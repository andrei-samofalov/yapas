import asyncio
import threading
from typing import Any, Hashable, NamedTuple, Optional

from yapas.core.abs.cache import AbstractCache

DEFAULT_TIMEOUT = 60


class CacheValue(NamedTuple):
    """Cache value impl."""
    expires: float
    value: Any


class TTLMemoryCache(AbstractCache):
    """TTL in-memory cache"""

    def __init__(self, timeout=DEFAULT_TIMEOUT, update_on_get: bool = True):
        self._timeout = timeout
        self._update_on_get = update_on_get
        self._storage: dict[Hashable, Any] = {}
        self._mutex = threading.RLock()
        self._hits = 0
        self._misses = 0

        loop = asyncio.get_event_loop()
        self._timer = loop.time

    def __str__(self):
        return f"<TTLMemoryCache hits={self._hits} misses={self._misses} length={len(self._storage)}>"

    def get(self, key):
        """Get a value from the storage.

        If key is presented but value is expired, delete key from the storage.
        """

        cache_value: Optional[CacheValue] = self._storage.get(key)
        if cache_value is None:
            self._misses += 1
            return cache_value

        if cache_value.expires < self._timer():
            self._misses += 1
            del self._storage[key]
            return None

        self._hits += 1
        if self._update_on_get:
            self.touch(key)

        return cache_value.value

    def set(self, key, value):
        """Set a new value to key"""
        with self._mutex:
            expires = self._timer() + self._timeout
            self._storage[key] = CacheValue(expires=expires, value=value)

    def touch(self, key):
        """Update expiration and return boolean on success"""
        try:
            with self._mutex:
                self.set(key, self._storage.pop(key))
        except KeyError:
            return False

        return True
