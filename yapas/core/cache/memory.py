import threading
import weakref

from yapas.core.abs.cache import AbstractCache


class WeakStr(str):
    pass


class InMemoryCache(AbstractCache):
    def __init__(self):
        self._cache = weakref.WeakKeyDictionary()
        self._mutex = threading.RLock()
        self._hits = 0
        self._misses = 0

    def __repr__(self):
        return f"<InMemoryCache hits={self._hits} misses={self._misses} length={len(self._cache)}>"

    def _prepare_key(self, k):
        return WeakStr(hash(k))

    def get(self, key):
        key = self._prepare_key(key)
        result = self._cache.get(key)
        if result is None:
            self._misses += 1
        else:
            self._hits += 1
        return result

    def set(self, key, value):
        key = self._prepare_key(key)
        print(f'{key!r}')
        with self._mutex:
            self._cache[key] = value
        print(f'{key!r} set {self._cache}')

    def touch(self, key):
        key = self._prepare_key(key)
        try:
            with self._mutex:
                self._cache[key] = self._cache.pop(key)
        except KeyError:
            return False

        return True
