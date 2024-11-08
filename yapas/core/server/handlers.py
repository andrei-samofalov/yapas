import pathlib
import signal
from logging import getLogger

from yapas.core.abs.handlers import AbstractHandler, TemplateHandler, GetMixin, ErrorHandler
from yapas.core.abs.messages import RawHttpMessage
from yapas.core.cache.memory import TTLMemoryCache
from yapas.core.client.socket import SocketClient
from yapas.core.constants import OK, WORKING_DIR
from yapas.core.exceptions import NotFoundError, InternalServerError
from yapas.core.signals import show_metrics
from yapas.core.statics import async_open

logger = getLogger('yapas.handlers')
cache = TTLMemoryCache(timeout=60)


class ProxyHandler(AbstractHandler):
    """Proxy handler for all requests"""

    async def dispatch(self, message: RawHttpMessage) -> RawHttpMessage:
        """Proxy handler, ignores ALLOWED METHODS"""
        _client = SocketClient()
        return await _client.raw(message)


class RestartHandler(TemplateHandler):
    """Restart handler. Restarts the server."""

    async def get_context(self) -> dict:
        return {"error_msg": "Restarting..."}

    async def get(self, _message: RawHttpMessage):
        signal.raise_signal(signal.SIGHUP)
        return RawHttpMessage(OK)


class MetricsHandler(AbstractHandler):
    """Metrics handler. Shows statistics in stdout."""

    async def get(self, _request: RawHttpMessage) -> RawHttpMessage:
        show_metrics.set()
        return RawHttpMessage(OK)


class IndexHandler(GetMixin, TemplateHandler):
    """Index template handler"""
    template = 'static/templates/index.html'


class NotFoundHandler(ErrorHandler):
    """Base Not Found handler"""
    error = NotFoundError


class InternalErrorHandler(ErrorHandler):
    """Base Internal Error handler"""
    error = InternalServerError


async def _static(static_path) -> RawHttpMessage:
    if (result := cache.get(static_path)) is not None:
        return result

    if not pathlib.Path(static_path).exists():
        raise NotFoundError()

    async with async_open(static_path) as f:
        result = RawHttpMessage(OK, body=await f.read())
        cache.set(static_path, result)
        return result


async def proxy_static(message: RawHttpMessage) -> RawHttpMessage:
    """Static files handler, uses TTLCache."""

    # todo переписать на нормальный хендлер сервера
    path = message.info.path.decode().removeprefix('/static')
    static_path = f'/var/www/static/ma-tool{path}'

    if "?" in static_path:
        # versioned static files
        static_path, *_ = static_path.split("?")

    return await _static(static_path)


async def server_static(message: RawHttpMessage) -> RawHttpMessage:
    """Server static files handler."""
    path = message.info.path.decode().replace('/server_static', './static')
    static_path = WORKING_DIR / path
    return await _static(static_path)
