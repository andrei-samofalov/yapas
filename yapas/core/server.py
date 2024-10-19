import asyncio
import inspect
import logging
import pathlib
import signal
import urllib.parse as urlparse
from asyncio import StreamReader, StreamWriter
from logging import getLogger
from typing import Optional

from yapas.core.signals import kill_event, handle_shutdown, handle_restart
from yapas.core.types import (
    Application, Message, Scope,
    EOF_BYTES,
    AppFactory, SPACE_BYTES
)


class Server:
    """Async Server implementation."""

    def __init__(self, host: str, port: int, app: Application | AppFactory) -> None:
        self._host = host
        self._port = port

        if inspect.isfunction(app):
            # this can be if app object is a factory
            app = app()

        self._app = app
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
            self.dispatch,
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

    async def dispatch(self, reader: StreamReader, writer: StreamWriter):
        if (first_line := await reader.readline()) in EOF_BYTES:
            return {'type': 'unhandled'}

        scope: Scope = {'type': "http"}
        method, path, protocol = first_line.decode().strip().split(' ')
        url = urlparse.urlparse(path)
        scope['method'] = method
        scope['scheme'] = url.scheme
        scope['path'] = url.path
        scope['root_path'] = url.hostname
        scope['query_string'] = url.query

        headers = []
        async for data in reader:
            if data in EOF_BYTES:
                reader.feed_eof()
                break
            name, _, val = data.partition(b':')
            headers.append((name, val))

        scope['headers'] = headers

        async def _receive() -> Message:

            raw_data = bytearray()
            if not reader.at_eof():
                raw_data += b'\r\n'
                raw_data += await reader.read()

            return {"type": "http.request", "body": raw_data, "more_body": False}

        async def _send(message: Message) -> None:
            await self.write_msg(writer, message)

        await self._app(scope, _receive, _send)

    async def write_msg(self, writer: StreamWriter, message: Message):
        """Write the message to the response"""
        if not "type" in message or 'http.response' not in message["type"]:
            raise RuntimeError

        self._log.debug(f'received message: {message}')
        event = message["type"]
        if 'start' in event:
            writer.write(b'HTTP/1.1 %d %s\r\n' % (message['status'], message.get('reason', b'')))

            for header in message['headers']:
                header: list[bytes]
                writer.write(b': '.join(header))
                writer.write(SPACE_BYTES)
            writer.write(SPACE_BYTES)
            await writer.drain()

        if 'body' in message:
            writer.write(message['body'])
            await writer.drain()

            if 'more_body' not in message:
                writer.close()
                await writer.wait_closed()

    async def start(self) -> None:
        """Start the server and wait for the kill event."""
        await self._start()
        await self._create_listeners()
        await kill_event.wait()

    async def shutdown(self) -> None:
        """Gracefully shutdown the server."""
        self._server.close()
        self._log.info('Server closed')
