from yapas.core.abs.enums import MessageType
from yapas.core.abs.messages import RawHttpMessage
from yapas.core.constants import HOST, PROXY_FORWARDED_FOR


class MessagesRootMiddleware:
    """Messages middleware. It converts StreamReader buffer to Message."""

    def __init__(self, dispatcher):
        self.dispatcher = dispatcher

    async def __call__(self, reader, *args, **kwargs):
        message = await RawHttpMessage.from_reader(reader)
        assert message.info.type is MessageType.REQUEST

        proxy = b'localhost:8000'
        message.add_header(HOST, proxy)
        message.add_header(PROXY_FORWARDED_FOR, proxy)
        message.add_header(b'Referer', proxy)

        call_next = await self.dispatcher.get_handler(message.info.path)
        return await call_next(message, *args, **kwargs)
