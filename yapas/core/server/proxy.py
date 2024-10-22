from asyncio import StreamReader, StreamWriter

from yapas.core.abs.dispatcher import ProxyHandler
from yapas.core.abs.enums import MessageType
from yapas.core.abs.messages import RawHttpMessage
from yapas.core.abs.server import BaseAsyncServer
from yapas.core.constants import HOST, PROXY_FORWARDED_FOR
from yapas.core.middlewares.metrics import metrics


class ProxyServer(BaseAsyncServer):
    """Proxy-based async server"""

    @metrics()
    async def dispatch(self, reader: StreamReader, writer: StreamWriter) -> None:
        message = await RawHttpMessage.from_reader(reader)
        assert message.info.type is MessageType.REQUEST

        proxy = b'localhost:8000'
        message.add_header(HOST, proxy)
        message.add_header(PROXY_FORWARDED_FOR, proxy)
        message.add_header(b'Referer', proxy)

        handler: ProxyHandler = await self.dispatcher.get_handler(message.info.path)

        response = await handler(message)

        if message.has_header(b'Set-Cookie'):
            value, *_ = message.get_header_value(b'Set-Cookie').split(b';', maxsplit=1)
            response.add_header(b'Cookie', value)


        await response.fill(writer)

        if not response.heep_alive():
            writer.close()
            await writer.wait_closed()

        return message, response
