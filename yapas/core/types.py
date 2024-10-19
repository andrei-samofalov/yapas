from typing import Any, Awaitable, MutableMapping, Callable, Protocol, runtime_checkable

EMPTY_BYTES = b""
SPACE_BYTES = b'\r\n'
EOF_BYTES = (EMPTY_BYTES, SPACE_BYTES)

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]


@runtime_checkable
class Application(Protocol):
    """An ASGI v2.5 application protocol"""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Dispatch the incoming request"""


ApplicationCallable = Callable[[Scope, Receive, Send], Awaitable[None]]
AppFactory = Callable[[...], Application]
