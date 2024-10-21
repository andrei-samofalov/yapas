from asyncio import StreamReader, StreamWriter

from yapas.core.abs.dispatcher import ProxyHandler
from yapas.core.abs.enums import MessageType
from yapas.core.abs.messages import RawHttpMessage
from yapas.core.abs.server import BaseAsyncServer


class ProxyServer(BaseAsyncServer):
    """Proxy-based async server"""

    async def dispatch(self, reader: StreamReader, writer: StreamWriter) -> None:
        message = await RawHttpMessage.from_reader(reader)
        assert message.type is MessageType.REQUEST

        handler: ProxyHandler = await self.dispatcher.get_handler(message.info.path)
        response = await handler(message)

        await response.fill(writer)

        if not response.heep_alive():
            writer.close()
            await writer.wait_closed()
