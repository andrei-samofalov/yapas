import asyncio
import pathlib
from functools import lru_cache, partial


@lru_cache
def _read(template: pathlib.Path):
    with open(template, "r") as f:
        return f.read()


class async_open:
    """Async version of open"""

    def __init__(self, file, mode='r', *args, **kwargs):
        self._file = file
        self._mode = mode
        self._args = args
        self._kwargs = kwargs
        self._opened_file = None
        self._closing_condition = asyncio.Event()

    async def __aenter__(self):
        loop = asyncio.get_event_loop()
        open_func = partial(open, self._file, self._mode, *self._args, **self._kwargs)
        self._opened_file = await loop.run_in_executor(None, open_func)
        return self._opened_file

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._opened_file.close()
        return True


async def render(template: pathlib.Path, **context):
    """Render a template file with optional context dict"""
    html_code = _read(template)

    if context:
        html_code = html_code.format(**context)

    return html_code


async def render_base(**context):
    """Render the base template file with context dict"""
    return await render(pathlib.Path(__file__).parent.parent / "static/base.html", **context)
