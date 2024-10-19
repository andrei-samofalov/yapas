import asyncio
import logging
import pathlib
from logging import getLogger
from typing import Optional

from yapas.core.dispatcher import Dispatcher

kill_event = asyncio.Event()


class Server:
    """Async Server implementation."""

    def __init__(self, host: str, port: int, dispatcher: Dispatcher) -> None:
        self._host = host
        self._port = port

        self._dispatcher = dispatcher
        self._static_path: Optional[str | pathlib.Path] = None

        self._log: logging.Logger = getLogger('async-server')

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

    async def start(self) -> None:
        """Start the server and wait for the kill event."""
        server = await self._create_server()
        self._log.info(f'Starting TCP server on {self._host}:{self._port}')

        await server.start_serving()
        await kill_event.wait()
