import pathlib
from functools import lru_cache


@lru_cache
def _read(template: pathlib.Path):
    with open(template, "r") as f:
        return f.read()


async def render(template: pathlib.Path, **context):
    """Render a template file with optional context dict"""
    html_code = _read(template)

    if context:
        html_code = html_code.format(**context)

    return html_code


async def render_base(**context):
    """Render the base template file with context dict"""
    return await render(pathlib.Path(__file__).parent.parent / "static/base.html", **context)
