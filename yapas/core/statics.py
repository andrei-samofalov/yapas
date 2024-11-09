import asyncio
import pathlib
from functools import partial


class AsyncOpener:  # noqa
    """Async version of open"""

    def __init__(self, file, mode='rb', *args, **kwargs):
        self._file = file
        self._mode = mode
        self._args = args
        self._kwargs = kwargs
        self._opened_file = None

        self._loop = asyncio.get_event_loop()
        open_func = partial(open, self._file, self._mode, *self._args, **self._kwargs)
        self._coro = self._coro_factory(open_func)

    @property
    def _coro_factory(self):
        return partial(self._loop.run_in_executor, None)

    async def read(self):
        return await self._coro_factory(self._opened_file.read)

    async def __aenter__(self):
        if self._opened_file is None:
            self._opened_file = await self._coro
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._opened_file:
            self._opened_file.close()
        self._opened_file = None


async def render(template: pathlib.Path, **context) -> bytes:
    """Render a template file with optional context dict"""
    async with async_open(template, mode="r") as f:
        html_code = await f.read()

    if context:
        html_code = html_code.format(**context)

    return html_code.encode()


async def render_base(**context):
    """Render the base template file with context dict"""
    return await render(
        pathlib.Path(__file__).parent.parent / "static/templates/base.html",
        **context,
    )


async_open = AsyncOpener
