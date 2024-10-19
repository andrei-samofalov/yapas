import logging
import urllib.parse as urlparse
from asyncio import StreamReader, StreamWriter
from http import HTTPMethod, HTTPStatus
from typing import Optional
from urllib.parse import ParseResult

from yapas.core import exceptions
from yapas.core.request import make_request, Request
from yapas.core.response import Response

EMPTY_BYTES = b""
SPACE_BYTES = b'\r\n'
EOF_STRINGS = (EMPTY_BYTES, SPACE_BYTES)


class Router:
    """Simple router implementation"""

    def __init__(self, dispatcher: Optional["Dispatcher"] = None) -> None:
        self._dispatcher = dispatcher
        self._path: Optional[str] = None
        self._parent: Optional["Router"] = None
        self._children: list['Router'] = []

    def register_router(self, path: str, router: "Router") -> None:
        """Register router as a child router"""
        executor = self._dispatcher or self._parent
        executor.register_router(path, router)
        self._children.append(router)
        router.register(self, path)

    def register(self, parent, self_path):
        """Register self to a route path"""
        self._path = self_path
        self._parent = parent

    def search_router(self, url: ParseResult):
        """Search a particular router for handling request by its path"""
        if self._path == url.path:
            return self

        for router in self._children:
            if router.search_router(url):
                return router

        return None

    def can_handle(self, method: HTTPMethod):
        """Return True if router can handle request, False otherwise"""
        return hasattr(self, method.lower())

    async def dispatch(self, request: Request) -> Response:
        """Dispatch request to handler"""
        router = self.search_router(request.url)
        if not router:
            raise exceptions.NotFoundError(request.url.path)

        if not router.can_handle(request.method):
            raise exceptions.MethodNotAllowed(request.method.name)

        handler = getattr(router, request.method.lower())
        return await handler(request)


class Dispatcher:
    """Dispatcher class for handle and routing requests"""

    def __init__(self) -> None:
        self._methods = ('GET', 'POST')
        self._log: logging.Logger = logging.getLogger("yapas.dispatcher")
        self.root_router: Optional[Router] = None
        self._routes: dict[str, Router] = {}

    def register_router(self, path: str, router: "Router"):
        """Register a router to route mapping"""
        if path in self._routes:
            raise exceptions.ImproperlyConfigured(f"{path} is already registered")

        self._routes[path] = router

    def register_root(self, router: "Router") -> None:
        """Register a router as a root router"""
        self.root_router = router
        router.register(self, '/')

    async def root_handler(self, reader: StreamReader, writer: StreamWriter):
        """Root handler for all requests"""

        try:
            if (request := await self._initialize_request(reader)) is None:
                return
            response = await self._dispatch(request)
        except Exception as e:
            response = await self._handle_exception(e)

        await self._write_response(writer, response)

    async def _initialize_request(self, reader: StreamReader):
        """Initialize request: parse protocol, path, method, headers and data,
        create and return a Request object."""

        if (first_line := await reader.readline()) in EOF_STRINGS:
            return

        method, path, protocol = first_line.decode().strip().split(' ')

        # we don't want to read request we can not handle
        if path not in self._routes:
            raise exceptions.NotFoundError(path)

        raw_data = bytearray()
        async for data in reader:
            if data in EOF_STRINGS:
                reader.feed_eof()
                break
            raw_data += data

        if not reader.at_eof():
            raw_data += b'\r\n'
            raw_data += await reader.read()

        url = urlparse.urlparse(path)
        return make_request(method, url, raw_data)

    @classmethod
    async def _write_response(cls, writer: StreamWriter, response: Response):
        """Write the Response to the Transport buffer and drain it."""

        writer.write(response.status_bytes())  # HTTP/1.1 200 OK
        for header in response.headers_bytes():
            writer.write(header)
        writer.write(SPACE_BYTES)

        if response.body:
            writer.write(response.body_bytes())
            writer.write(SPACE_BYTES)

        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def _dispatch(self, request: Request) -> Response:
        """Handle request"""
        try:
            return await self.root_router.dispatch(request)
        except Exception as exception:
            return await self._handle_exception(exception)

    async def _handle_exception(self, exc: Exception) -> Response:
        if not isinstance(exc, exceptions.HTTPException):
            return await self._unhandled(exc)

        self._log.warning(f"{exc.args[0]}: {exc.status} {exc.status.name}")
        return Response(status=exc.status)

    async def _unhandled(self, exc: Exception) -> Response:
        self._log.exception(exc)
        return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)

    async def perform_checks(self):
        """Perform checks on the startup"""
        if not self.root_router:
            raise exceptions.ImproperlyConfigured("You must register the root router")
