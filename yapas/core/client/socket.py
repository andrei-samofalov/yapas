import asyncio
import contextlib
import socket
import ssl
from typing import Optional

from yapas.core.abs.client import AbstractSession, AbstractClient
from yapas.core.abs.messages import RawHttpMessage
from yapas.core.constants import EMPTY_BYTES


class SocketSession(AbstractSession):
    """Base session class."""

    def __init__(
        self,
        base_url: str = '0.0.0.0:8000',
        ssl_context: Optional[ssl.SSLContext] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> None:
        super().__init__(base_url, ssl_context, loop)
        self._conn: Optional[socket.socket] = None

    async def _close(self):
        conn = self._conn
        conn.close()
        self._conn = None

    async def _connect(self):
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        await self._loop.sock_connect(self._conn, (self._host, self._port))

    async def _wrapped_sock(self):
        if self._ssl_context is None:
            return self._conn
        return self._ssl_context.wrap_socket(self._conn, server_hostname=self._host)

    async def request(self, message: RawHttpMessage) -> RawHttpMessage:
        """Send raw request bytes via stram socket and read socket buffer for response"""
        conn = await self._wrapped_sock()  # ssl context
        await self._loop.sock_sendall(conn, message.raw_bytes)

        response = EMPTY_BYTES
        while True:
            data = await self._loop.sock_recv(conn, 4096)
            response += data
            if data == EMPTY_BYTES:
                break

        return await RawHttpMessage.from_bytes(response)


class SocketClient(AbstractClient):
    """Socket-based client."""

    @contextlib.asynccontextmanager
    async def get_session(self):
        async with SocketSession(base_url=self._base_url, ssl_context=self._ssl_ctx) as session:
            yield session
