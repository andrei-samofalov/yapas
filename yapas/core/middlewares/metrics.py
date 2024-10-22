import asyncio
import logging
import threading
from threading import Thread
from typing import Callable, Awaitable

from yapas.core.abs.messages import RawHttpMessage
from yapas.core.abs.server import BaseAsyncServer
from yapas.core.signals import prepare_shutdown

StreamReader = asyncio.StreamReader
StreamWriter = asyncio.StreamWriter
CallbackResponse = tuple[RawHttpMessage, RawHttpMessage]

Decorated = Callable[[BaseAsyncServer, StreamReader, StreamWriter], Awaitable[CallbackResponse]]
show_metrics = threading.Event()


# todo переделать на Middleware, это не работает сейчас, как нужно
class MessageMetrics:
    """Class for logging and writing metrics"""

    def __init__(self):
        self._counter = 0
        self._response_time = 0
        self._log = logging.getLogger('yapas.metrics')
        self._loop = asyncio.get_event_loop()

    def _show_metrics(self):
        # todo wtf,
        while not prepare_shutdown.is_set():
            # daemonic closes the loop
            show_metrics.wait()
            self._log.info(
                f'total requests: {self._counter} | '
                f'average response time: {self._response_time / self._counter:.4f} ms'
            )
            show_metrics.clear()

    def __call__(self, dispatch_cb: Decorated) -> Decorated:
        Thread(target=self._show_metrics, name='metrics', daemon=True).start()

        async def _decorated(_self, reader: StreamReader, writer: StreamWriter) -> CallbackResponse:
            self._counter += 1
            now = self._loop.time()
            req, resp = await dispatch_cb(_self, reader, writer)
            elapsed = self._loop.time() - now

            _self._log.info(f'{req!r} - {resp!r}: {elapsed:.4f} ms')  # noqa
            self._response_time += elapsed
            return req, resp

        return _decorated


metrics = MessageMetrics
