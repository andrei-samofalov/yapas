import json
from http import HTTPMethod
from typing import NamedTuple
from urllib.parse import ParseResult as URLParseResult


class Request(NamedTuple):
    """Request representation."""
    method: HTTPMethod
    url: URLParseResult
    headers: dict
    body: bytes

    def data(self) -> dict:
        """Return json parsed body"""
        return json.loads(self.body.decode('utf-8'))


def make_request(method, url, data: bytes) -> Request:
    """Create and return a request object with parsed headers and body."""
    headers_gen = _headers_parse_generator()
    next(headers_gen)
    headers_and_body = iter(data.split(b'\r\n'))
    for chunk in headers_and_body:
        if chunk == b'':
            break
        headers_gen.send(chunk)
    headers = headers_gen.send(None)
    headers_gen.close()

    return Request(
        method=method,
        url=url,
        headers=headers,
        body=b''.join(headers_and_body),
    )


def _headers_parse_generator():
    eof_bytes = b'\r\n'
    headers = {}

    while True:
        byte_str: bytes = yield
        if byte_str is None:
            yield headers
        if byte_str == eof_bytes:
            break
        name, _, value = byte_str.decode().partition(":")
        headers[name] = value
