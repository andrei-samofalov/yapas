from abc import ABC
from typing import Callable, Awaitable

from yapas.conf.dispatcher import ALLOWED_METHODS
from yapas.core.abs.enums import MessageType
from yapas.core.abs.messages import RawHttpMessage
from yapas.core.constants import WORKING_DIR, OK
from yapas.core.exceptions import MethodNotAllowed, HTTPException
from yapas.core.statics import render

DEFAULT_CONTEXT = {}
HandlerCallable = Callable[[RawHttpMessage], Awaitable[RawHttpMessage]]


class AbstractHandler(ABC):
    """Abstract base class for handlers."""

    def __init__(self, request: RawHttpMessage):
        self._request = request
        self._context = DEFAULT_CONTEXT

    @classmethod
    def as_view(cls):
        """Closure for handling requests"""

        def _view(request):
            self = cls(request)
            return self.dispatch(request)

        return _view

    async def _get_handler(self, method: bytes):
        """Return handler for the given method.

        :raises MethodNotAllowed: If method is not allowed, or not implemented.
        """
        if (
            (method_str := method.decode().lower()) not in ALLOWED_METHODS
            or not hasattr(self, method_str)
        ):
            raise MethodNotAllowed()
        return getattr(self, method_str)

    async def dispatch(self, request: RawHttpMessage) -> RawHttpMessage:
        """Dispatch request to the appropriate handler."""
        assert request.info.type is MessageType.REQUEST
        _handler = await self._get_handler(request.info.method)
        response = await _handler(request)
        assert isinstance(response, RawHttpMessage) and response.info.type is MessageType.RESPONSE
        return response


class TemplateHandler(AbstractHandler):
    """Template handler."""
    template: str = 'static/templates/base.html'

    async def render_template(self):
        """Render and return template body."""
        context = await self.get_context()
        return await render(template=WORKING_DIR / self.template, **context)

    async def get_context(self) -> dict:
        """Return the context dict for given request."""
        return self._context

    async def dispatch(self, request: RawHttpMessage):
        response = await super().dispatch(request)
        template = await self.render_template()
        await response.add_body(template)
        return response


class ErrorHandler(TemplateHandler):
    error: HTTPException

    async def get_context(self) -> dict:
        return {'error_msg': self.error.status.description}

    async def get(self, _request: RawHttpMessage) -> RawHttpMessage:
        return await RawHttpMessage.from_bytes(buffer=self.error.as_bytes())


class GetMixin:
    """Mixin for simple get response"""
    async def get(self, _request: RawHttpMessage) -> RawHttpMessage:
        return RawHttpMessage(OK)
