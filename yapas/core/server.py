import asyncio
import logging
import pathlib
import signal
from logging import getLogger
from typing import Optional

from yapas.core.dispatcher import Dispatcher
from yapas.core.signals import kill_event, handle_shutdown, handle_restart


class Server:
    """Async Server implementation."""

    def __init__(self, host: str, port: int, dispatcher: Dispatcher) -> None:
        self._host = host
        self._port = port

        self._dispatcher = dispatcher
        self._static_path: Optional[str | pathlib.Path] = None

        self._log: logging.Logger = getLogger('yapas.server')
        self._server: Optional[asyncio.Server] = None

    def add_static_path(self, path: str | pathlib.Path) -> None:
        """Add static path to serve from"""
        # validation
        if isinstance(path, str):
            path = pathlib.Path(path)

        if not path.exists():
            path.mkdir(parents=True)

        self._static_path = path

    async def _create_server(self):
        """Create and return asyncio Server without starting it."""
        return await asyncio.start_server(
            self._dispatcher.root_handler,
            self._host,
            self._port,
            start_serving=False,
        )

    async def _start(self):
        if self._server is not None:
            await self.shutdown()
            self._log.info(f'Restarting...')

        self._server = await self._create_server()
        self._log.info(f'Starting TCP server on {self._host}:{self._port}')
        await self._server.start_serving()

    async def _create_listeners(self):
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
            lambda: asyncio.create_task(handle_restart(self)),
        )

    async def start(self) -> None:
        """Start the server and wait for the kill event."""
        await self._start()
        await self._create_listeners()
        await kill_event.wait()

    async def shutdown(self) -> None:
        """Gracefully shutdown the server."""
        self._server.close()
        self._log.info('Server closed')
