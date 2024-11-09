from asyncio import StreamReader, StreamWriter
from typing import Optional

from yapas.core.abs.enums import MessageType
from yapas.core.abs.handlers import HandlerCallable
from yapas.core.abs.messages import RawHttpMessage
from yapas.core.abs.server import AbstractAsyncServer
from yapas.core.constants import HOST, PROXY_FORWARDED_FOR, REFERER
from yapas.core.exceptions import HTTPException, DispatchException, InternalServerError
from yapas.core.middlewares.metrics import metrics

StackCall = tuple[RawHttpMessage, RawHttpMessage] | tuple[None, None]


class ProxyServer(AbstractAsyncServer):
    """Proxy-based async server"""

    async def read_request(self, reader: StreamReader):
        request = await RawHttpMessage.from_reader(reader)
        assert request
        assert request.info.type is MessageType.REQUEST

        # todo вынести это
        proxy = b'localhost:8000'
        request.add_header(HOST, proxy)
        request.add_header(PROXY_FORWARDED_FOR, proxy)
        request.add_header(REFERER, proxy)

        return request

    @metrics()
    async def middleware_stack(
        self,
        reader: StreamReader,
        writer: StreamWriter,
    ) -> Optional[StackCall]:
        """Read a Request and create a Response object through the middleware stack"""

        try:
            request = await self.read_request(reader)
        except DispatchException as e:
            self._log.exception(e)
            return None, None

        handler: HandlerCallable = await self.dispatcher.get_handler(path=request.info.path)

        try:
            response = await handler(request)
        except HTTPException as exc:
            response = await RawHttpMessage.from_bytes(buffer=exc.as_bytes())
        except Exception as e:
            self._log.exception(e)
            response = await RawHttpMessage.from_bytes(buffer=InternalServerError.as_bytes())

        if request.has_header(b'Set-Cookie'):
            value, *_ = request.get_header_value(b'Set-Cookie').split(b';', maxsplit=1)
            response.add_header(b'X-CSRFToken', value)

        await response.fill(writer)

        if not response.heep_alive():
            writer.close()
            await writer.wait_closed()

        return request, response

    async def dispatch(self, reader: StreamReader, writer: StreamWriter) -> None:
        await self.middleware_stack(reader, writer)
