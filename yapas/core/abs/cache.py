from typing import Protocol, Awaitable


class AbstractCache[_KT, _VT](Protocol):

    async def get(self, key: _KT) -> _VT: ...

    async def set(self, key: _KT, value: _VT) -> None: ...

    async def touch(self, key: _KT) -> bool: ...
