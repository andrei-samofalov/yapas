from abc import abstractmethod, ABC
from typing import Self

from yapas.conf.parser import ConfParser
from yapas.core.abs.handlers import HandlerCallable
from yapas.core.constants import EMPTY_BYTES
from yapas.core.server import handlers

NOT_FOUND_HANDLE = handlers.NotFoundHandler.as_view()


class AbstractDispatcher(ABC):
    """Abstract base class for all dispatchers."""

    def __init__(self):
        # like nginx locations
        self._locations: dict[bytes, HandlerCallable] = {}

    @classmethod
    @abstractmethod
    def from_conf(cls, conf: ConfParser) -> Self:
        """Create a Dispatcher instance from a configuration file."""

    def add_location(self, path: str, handler: HandlerCallable):
        """Add location to listen and proxy pass to"""
        if not path.startswith('/'):
            path = f"/{path}"
        self._locations[path.encode()] = handler

    async def get_handler(self, path: bytes) -> HandlerCallable:
        """Find handler for particular request path"""

        if path == EMPTY_BYTES:
            return NOT_FOUND_HANDLE

        assert path.startswith(b'/'), path

        for loc, handler in self._locations.items():
            if path == loc:
                return handler

            elif loc.endswith(b'*') and path.startswith(loc.removesuffix(b'*')):
                return handler

        return NOT_FOUND_HANDLE
