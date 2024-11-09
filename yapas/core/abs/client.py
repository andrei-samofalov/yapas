import asyncio
import contextlib
import ssl
from abc import abstractmethod, ABC
from logging import getLogger
from typing import Optional, Self, Protocol, Any, final
from urllib.parse import urlparse

from yapas.core.abs.messages import RawHttpMessage

logger = getLogger('yapas.core.client')
DEFAULT_CLIENT_TIMEOUT = 10


class SessionProtocol(Protocol):
    """Session impl"""

    async def request(self, *args, **kwargs) -> Any:
        """Send request"""


class AbstractSession(ABC):
    """Base session class."""

    def __init__(
        self,
        base_url: str = '0.0.0.0:8000',
        ssl_context: Optional[ssl.SSLContext] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        timeout: Optional[float] = DEFAULT_CLIENT_TIMEOUT,
    ) -> None:
        url = urlparse(base_url)

        self._base_url = base_url
        self._host = url.hostname
        self._port = url.port

        self._ssl_context = ssl_context
        self._loop = loop or asyncio.get_event_loop()
        self._timeout = timeout

    async def __aenter__(self) -> Self:
        await self._connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close()

    @abstractmethod
    async def _close(self) -> None:
        """Close the session"""
        raise NotImplementedError

    @abstractmethod
    async def _connect(self):
        """Perform the connection"""
        raise NotImplementedError

    @abstractmethod
    async def request(self, message: RawHttpMessage) -> RawHttpMessage:
        """Send raw request bytes via stram socket and read socket buffer for response"""


class AbstractClient(ABC):
    """The base http client class."""

    def __init__(
        self,
        base_url: str = 'http://localhost:8000',
        ssl_context: Optional[ssl.SSLContext] = None
    ) -> None:
        self._base_url = base_url
        self._ssl_ctx: Optional[ssl.SSLContext] = ssl_context

    @abstractmethod
    @contextlib.asynccontextmanager
    async def get_session(self) -> SessionProtocol:
        """Return a Session instance"""
        raise NotImplementedError

    async def _raw_request(self, message: RawHttpMessage):
        """Send raw request bytes"""
        async with self.get_session() as session:
            return await session.request(message)

    @final
    async def raw(self, message: RawHttpMessage):
        """Send Raw request and return response bytes"""
        return await self._raw_request(message)
