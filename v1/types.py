from typing import Any, Awaitable, MutableMapping, Callable, Protocol, runtime_checkable, \
    NamedTuple, Optional


def _getitem(self, item, default=None):
    try:
        return self.__getattribute__(item)
    except AttributeError:
        return default


class Message(NamedTuple):
    """A NamedTuple with getattr impl that represents a message."""

    type: str
    body: Optional[bytes] = None
    more_body: bool = False
    status: Optional[int] = 200
    headers: Optional[list[tuple[bytes, bytes]]] = None

    __getitem__ = _getitem
    get = _getitem

    @classmethod
    def fromkeys(cls, **kwargs):
        """Create a Message instance from kwargs."""
        return cls(**kwargs)


Scope = MutableMapping[str, Any]
ASGIMessage = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message | ASGIMessage], Awaitable[None]]


@runtime_checkable
class Application(Protocol):
    """An ASGI v2.5 application protocol"""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Dispatch the incoming request"""


ApplicationCallable = Callable[[Scope, Receive, Send], Awaitable[None]]
AppFactory = Callable[[...], Application]
