import asyncio
import copy
from dataclasses import dataclass, field
from logging import getLogger
from typing import Any, Hashable, Optional

from yapas.core.abs.cache import AbstractCache
from yapas.core.signals import kill_event

logger = getLogger('cache.memory')
DEFAULT_TIMEOUT = 60


@dataclass(slots=True, eq=False)
class CacheValue:
    """Cache value impl."""
    expires: float
    value: Any = field(compare=False)


class TTLMemoryCache[_KT, _VT](AbstractCache):
    """TTL in-memory cache"""

    def __init__(self, timeout=DEFAULT_TIMEOUT, update_on_get: bool = True):
        self._timeout = timeout
        self._update_on_get = update_on_get
        self._storage: dict[Hashable, Any] = {}
        self._mutex = asyncio.Lock()
        self._hits = 0
        self._misses = 0

        loop = asyncio.get_event_loop()
        self._timer = loop.time
        self._last_clean = self._timer()

        asyncio.ensure_future(self._cleanup_task())

    def __str__(self):
        return f"<TTLMemoryCache hits={self._hits} misses={self._misses} length={len(self._storage)}>"

    async def get(self, key: _KT) -> Optional[_VT]:
        """Get a value from the storage.

        If key is presented but value is expired, delete key from the storage.
        """
        # self._maybe_cleanup()

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
            await self._update_expiry(key)

        return cache_value.value

    async def set(self, key: _KT, value: _VT) -> None:
        """Set a new value to key"""
        async with self._mutex:
            expires = self._timer() + self._timeout
            self._storage[key] = CacheValue(expires=expires, value=value)

    async def _update_expiry(self, key: _KT) -> None:
        async with self._mutex:
            self._storage[key].expires = self._timer() + self._timeout

    async def touch(self, key: _KT) -> bool:
        """Update expiration and return boolean on success"""
        try:
            await self._update_expiry(key)
        except (KeyError, AttributeError):
            return False

        return True

    async def _cleanup_task(self):
        logger.info(f'starting cleanup task')
        while kill_event.is_set() is False:
            await asyncio.sleep(0)
            now = self._timer()
            if not len(self._storage) or now - self._last_clean < self._timeout:
                continue

            deleted = 0
            _storage = copy.deepcopy(self._storage)
            for k, val in _storage.items():
                if val.expires < now:
                    del self._storage[k]
                    deleted += 1

            logger.debug(f'cleanup task run finished, deleted {deleted} items')
            self._last_clean = now

        else:
            logger.info(f'cleanup task stopped')


# for async init with running loop
cache: TTLMemoryCache


async def init_cache() -> None:
    global cache
    cache = TTLMemoryCache()
