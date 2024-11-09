import inspect
import pathlib
import ssl
import urllib.parse as urlparse
from asyncio import StreamReader, StreamWriter
from typing import Optional

from v1.dispatcher import Dispatcher
from v1.types import (
    Application,
    AppFactory,
    ASGIMessage,
    Message,
    Scope,
)
from yapas.core import exceptions
from yapas.core.abs.server import AbstractAsyncServer
from yapas.core.constants import (

    EOF_BYTES,
    NEWLINE_BYTES, EMPTY_BYTES, OK,
)
from yapas.core.constants import WORKING_DIR


class ASGIServer(AbstractAsyncServer):
    """Async Server implementation."""

    def __init__(
        self,
        dispatcher: Dispatcher,
        host: Optional[str] = '0.0.0.0',
        port: Optional[int] = 80,
        root: Optional[str] = '/',
        log_level: Optional[str] = 'DEBUG',
        ssl_context: Optional[ssl.SSLContext] = None,
        ssl_handshake_timeout: Optional[int] = None,
        app: Optional[Application | AppFactory] = None,
    ) -> None:
        super().__init__(
            dispatcher=dispatcher,
            host=host,
            port=port,
            log_level=log_level,
            ssl_context=ssl_context,
            ssl_handshake_timeout=ssl_handshake_timeout,
        )

        if inspect.isfunction(app):
            # this can be if app object is a factory
            app = app()

        self._app = app
        self._static_prefix = '/static'
        self._static_path: Optional[str | pathlib.Path] = WORKING_DIR / self._static_prefix

    def add_static_path(self, path: str | pathlib.Path) -> None:
        """Add static path to serve from"""
        # validation
        posix_path = path
        if isinstance(path, str):
            posix_path = path if path.startswith('/') else WORKING_DIR / path

        if not posix_path.exists():
            posix_path.mkdir(parents=True)

        self._static_path = str(posix_path)

    async def dispatch(self, reader: StreamReader, writer: StreamWriter) -> None:
        """Dispatch an incoming request"""
        if (first_line := await reader.readline()) in EOF_BYTES:
            return

        scope: Scope = {'type': "http"}
        method, path, protocol = first_line.decode().strip().split(' ')
        url = urlparse.urlparse(path)
        scope['method'] = method
        scope['scheme'] = url.scheme
        scope['path'] = url.path
        scope['root_path'] = url.hostname
        scope['query_string'] = url.query

        if url.path == self._root:
            return await self.serve_files(writer, '/static/templates/index.html')

        if url.path.startswith(self._static_prefix):
            return await self.serve_files(writer, url.path)

        headers = []
        reader_gen = aiter(reader)
        async for data in reader_gen:
            if data in EOF_BYTES:
                reader.feed_eof()
                break
            name, _, val = data.strip().partition(b':')
            headers.append((name, val))

        scope['headers'] = headers

        async def _receive() -> Message:

            raw_data = bytearray()
            if not reader.at_eof():
                raw_data += NEWLINE_BYTES
                raw_data += await reader.read()

            return Message(type="http.request", body=raw_data)

        async def _send(message: ASGIMessage) -> None:
            await self.write_msg(writer, Message.fromkeys(**message))

        await self._app(scope, _receive, _send)

    async def write_msg(self, writer: StreamWriter, message: Message):
        """Write the message to the response"""
        if not message.type or 'http.response' not in message.type:
            raise RuntimeError

        self._log.debug(f'received message: {message}')
        event = message.type
        if 'start' in event:
            writer.write(
                b'HTTP/1.1 %d %s\r\n' % (message.status, message.get('reason', EMPTY_BYTES)))

            for header in message.headers:
                writer.write(b': '.join(header))

            writer.write(NEWLINE_BYTES * 2)
            await writer.drain()

        if message.body:
            writer.write(message.body)
            await writer.drain()

            if not message.more_body:
                writer.close()
                await writer.wait_closed()

    async def serve_files(self, writer: StreamWriter, path: str | pathlib.Path) -> None:
        """Serve files from static path"""
        # this is awful
        path = f"{self._static_path}{path.replace(self._static_prefix, "")}"
        error = None
        if not pathlib.Path(path).exists():
            error = exceptions.NotFoundError()
        else:
            try:
                async with static.async_open(path, mode='rb') as f:
                    data = await f.read()
            except Exception as e:
                self._log.exception(e)
                error = exceptions.InternalServerError()

        if error:
            writer.write(error.as_bytes())
            writer.write(NEWLINE_BYTES)  # <- instead of headers
            writer.write(NEWLINE_BYTES)
        else:
            writer.write(OK)
            writer.write(NEWLINE_BYTES)  # <- instead of headers
            writer.write(NEWLINE_BYTES)
            writer.write(data)

        await writer.drain()
        writer.close()
        await writer.wait_closed()
