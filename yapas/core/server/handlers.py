import pathlib
import signal
from logging import getLogger

from yapas.core.abs.messages import RawHttpMessage
from yapas.core.cache.memory import TTLMemoryCache
from yapas.core.client.socket import SocketClient
from yapas.core.constants import NOT_FOUND, OK, INTERNAL_ERROR
from yapas.core.middlewares.metrics import show_metrics
from yapas.core.statics import async_open, render_base

logger = getLogger('yapas.handlers')

cache = TTLMemoryCache(timeout=60)


async def proxy(message: RawHttpMessage) -> RawHttpMessage:
    """Proxy handler"""
    _client = SocketClient()
    return await _client.raw(message)


async def metrics(_message: RawHttpMessage) -> RawHttpMessage:
    """Metrics handler"""
    show_metrics.set()
    return RawHttpMessage(OK)


async def static(message: RawHttpMessage) -> RawHttpMessage:
    """Static files handler, uses TTLCache."""

    # todo переписать на нормальный хендлер сервера
    path = message.info.path.decode().removeprefix('/static')
    static_path = f'/var/www/static/ma-tool{path}'

    if "?" in static_path:
        # versioned static files
        static_path, *_ = static_path.split("?")

    if (result := cache.get(static_path)) is not None:
        return result

    if not pathlib.Path(static_path).exists():
        return RawHttpMessage(NOT_FOUND)  # todo abs

    try:
        async with async_open(static_path) as f:
            result = RawHttpMessage(OK, body=await f.read())
            cache.set(static_path, result)
            return result
    except Exception as e:
        logger.exception(e)
        return RawHttpMessage(INTERNAL_ERROR)


async def not_found(message: RawHttpMessage) -> 'RawHttpMessage':
    """Not found handler"""
    template = await render_base(
        error_msg=f"Page {message.info.path.strip().decode()} not found on this server"
    )
    return RawHttpMessage(OK, body=template)


async def restart(_message: RawHttpMessage):
    """Restart handler"""
    signal.raise_signal(signal.SIGHUP)
    template = await render_base(error_msg=f"Restarting...")
    return RawHttpMessage(OK, body=template)
