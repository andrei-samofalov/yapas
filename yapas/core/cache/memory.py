import asyncio
import copy
import threading
from dataclasses import dataclass, field
from typing import Any, Hashable, Optional

from yapas.core.abs.cache import AbstractCache

DEFAULT_TIMEOUT = 60


@dataclass(slots=True, eq=False)
class CacheValue:
    """Cache value impl."""
    expires: float
    value: Any = field(compare=False)


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
        self._last_clean = self._timer()

    def __str__(self):
        return f"<TTLMemoryCache hits={self._hits} misses={self._misses} length={len(self._storage)}>"

    def get(self, key):
        """Get a value from the storage.

        If key is presented but value is expired, delete key from the storage.
        """
        self._maybe_cleanup()

        cache_value: Optional[CacheValue] = self._storage.get(key)
        if cache_value is None:
            self._misses += 1
            return cache_value

        # this rarely can be if cleanup's self._timer() < new self._timer()
        if cache_value.expires < self._timer():
            self._misses += 1
            del self._storage[key]
            return None

        self._hits += 1
        if self._update_on_get:
            self._update_expiry(key)

        return cache_value.value

    def set(self, key, value):
        """Set a new value to key"""
        with self._mutex:
            expires = self._timer() + self._timeout
            self._storage[key] = CacheValue(expires=expires, value=value)

    def _update_expiry(self, key):
        with self._mutex:
            self._storage[key].expires = self._timer() + self._timeout

    def touch(self, key):
        """Update expiration and return boolean on success"""
        try:
            self._update_expiry(key)
        except (KeyError, AttributeError):
            return False

        return True

    def _maybe_cleanup(self):
        """Clean expired keys if last clean was later than configured timeout"""
        with self._mutex:
            now = self._timer()

            if now - self._last_clean < self._timeout:
                return

            _storage = copy.deepcopy(self._storage)
            for k, val in _storage.items():
                if val.expires < now:
                    del self._storage[k]

            self._last_clean = now
