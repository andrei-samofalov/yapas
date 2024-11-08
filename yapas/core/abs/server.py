import asyncio
import logging
import os
import signal
import ssl
from abc import abstractmethod, ABC
from asyncio import StreamReader, StreamWriter
from typing import Optional

from yapas.core.abs.dispatcher import AbstractDispatcher
from yapas.core.signals import kill_event, handle_shutdown, handle_restart


class AbstractAsyncServer(ABC):
    """Async Server implementation."""

    def __init__(
        self,
        dispatcher: AbstractDispatcher,
        host: Optional[str] = '0.0.0.0',
        port: Optional[int] = 8070,
        log_level: Optional[str] = 'DEBUG',
        ssl_context: Optional[ssl.SSLContext] = None,
        ssl_handshake_timeout: Optional[int] = None,
    ) -> None:
        """
        :param dispatcher: a Dispatcher instance with configured locations
        :param host: host to bind to
        :param port: port to bind to
        :param log_level: logging level, it would be passed to server logger directly
        :param ssl_context: SSL context to use, defaults to None
        :param port: port listen to, defaults to 80
        """
        self.dispatcher = dispatcher
        self._host = host
        self._port = port
        self._ssl_context = ssl_context
        self._ssl_handshake_timeout = ssl_handshake_timeout

        self._log: logging.Logger = logging.getLogger('yapas.server')
        self._log.setLevel(log_level.upper())
        self._server: Optional[asyncio.Server] = None

    async def _create_server(self):
        """Create and return asyncio Server without starting it."""
        return await asyncio.start_server(
            self.dispatch,
            self._host,
            self._port,
            ssl_handshake_timeout=self._ssl_handshake_timeout,
            start_serving=False,
        )

    async def _start(self):
        """Create asyncio.Server and start serving.
        If server is already running, restart it.
        """
        if self._server is not None:
            await self.shutdown()
            self._log.info(f'Restarting...')

        self._server = await self._create_server()
        self._log.info(f'Starting TCP server on {self._host}:{self._port} pid {os.getpid()}')
        await self._server.start_serving()

    async def _create_listeners(self):
        """Create the loop listeners for SIGINT, SIGTERM (shutdown)
        and SIGHUP (restart)
        """
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(
                    handle_shutdown(s.name, self)
                ),
            )
        loop.add_signal_handler(
            signal.SIGHUP,
            lambda *_: asyncio.create_task(handle_restart(self)),
        )

    @abstractmethod
    async def dispatch(self, reader: StreamReader, writer: StreamWriter) -> None:
        """Dispatch an incoming request"""
        raise NotImplementedError

    async def start(self) -> None:
        """Start the server and wait for the kill event."""
        await self._start()
        await self._create_listeners()
        await kill_event.wait()

    async def shutdown(self) -> None:
        """Gracefully shutdown the server."""
        server = self._server
        if server is None:
            return

        server.close()
        self._server = None
        self._log.info('Server closed')
