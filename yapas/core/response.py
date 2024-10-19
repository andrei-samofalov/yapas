from http import HTTPStatus
from typing import NamedTuple

JsonStr = str


class Response(NamedTuple):
    """Response implementation"""
    status: HTTPStatus
    headers: dict = {}
    body: JsonStr = ""

    def status_bytes(self):
        """Return a bytes representation of the status."""
        return b'HTTP/1.1 %d %s\r\n' % (self.status.value, self.status.name.encode())

    def headers_bytes(self):
        """Generate a bytes representation of the headers."""
        for header_name, header_value in self.headers.items():
            yield b'%s: %s\r\n' % (header_name.encode(), header_value.encode())

    def body_bytes(self) -> bytes:
        """Return the body of the response."""
        return self.body.encode()
