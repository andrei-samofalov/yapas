from abc import abstractmethod, ABC
from typing import Callable, Awaitable
from typing import Self

from yapas.conf.parser import ConfParser
from yapas.core.abs.messages import RawHttpMessage
from yapas.core.constants import EMPTY_BYTES
from yapas.core.server import handlers

ProxyHandler = Callable[[RawHttpMessage], Awaitable[RawHttpMessage]]


class AbstractDispatcher(ABC):
    """Abstract base class for all dispatchers."""

    def __init__(self):
        # like nginx locations
        self._locations: dict[bytes, ProxyHandler] = {}

    @classmethod
    @abstractmethod
    def from_conf(cls, conf: ConfParser) -> Self:
        """Create a Dispatcher instance from a configuration file."""

    def add_location(self, path: str, handler: ProxyHandler):
        """Add location to listen and proxy pass to"""
        if not path.startswith('/'):
            path = f"/{path}"
        self._locations[path.encode()] = handler

    async def get_handler(self, path: bytes) -> ProxyHandler:
        """Find handler for particular request path"""
        if path == EMPTY_BYTES:
            return handlers.not_found

        assert path.startswith(b'/'), path

        for loc, handler in self._locations.items():
            if path.startswith(loc):
                return handler

        return handlers.not_found
