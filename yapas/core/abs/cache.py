from typing import Protocol


class AbstractCache[_KT, _VT](Protocol):

    def get(self, key: _KT) -> _VT: ...

    def set(self, key: _KT, value: _VT) -> None: ...

    def touch(self, key: _KT) -> bool: ...
