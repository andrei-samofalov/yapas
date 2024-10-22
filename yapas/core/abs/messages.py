from asyncio import StreamReader, StreamWriter
from functools import cached_property
from typing import Optional, NamedTuple

from yapas.core.abs.enums import MessageType
from yapas.core.constants import SPACE_BYTES, EMPTY_BYTES, CONNECTION, KEEP_ALIVE


class _StatusLine(NamedTuple):
    type: MessageType
    protocol: bytes
    method: Optional[bytes] = None
    path: Optional[bytes] = None
    status: Optional[bytes] = None
    reason: Optional[bytes] = None

    @classmethod
    def from_bytes(cls, b: bytes):
        """Read the status line and create status line output.

        Req: b'GET / HTTP/1.1'
        Resp: b'HTTP/1.1 200 OK'
        """
        parts: list[bytes] = b.strip().split(maxsplit=2)
        assert len(parts) == 3, parts
        is_resp = parts[0].startswith(b"HTTP/1.")

        if is_resp:
            # Response message
            type_, protocol, status, reason = MessageType.RESPONSE, *parts  # noqa
            method, path = None, None
        else:
            # Request message
            type_, method, path, protocol = MessageType.REQUEST, *parts  # noqa
            status, reason = None, None

        return cls(type_, protocol, method, path, status, reason)


class RawHttpMessage:
    """A raw http message."""

    def __init__(
        self,
        f_line: bytes,
        *,
        headers: Optional[list[list[bytes]]] = None,
        body: Optional[bytes] = EMPTY_BYTES
    ) -> None:
        self._f_line = f_line
        self._info = _StatusLine.from_bytes(self._f_line)

        # todo headers class
        self._headers = {name.strip(): val.strip() for name, val in headers} if headers else {}
        self._body = body

    @classmethod
    async def from_bytes(cls, buffer: bytes):
        """Create a Message from bytes"""
        parts = buffer.split(SPACE_BYTES)
        f_line, parts = parts[0], parts[1:]

        headers = []
        body = b''
        for index, chunk in enumerate(parts):
            if chunk == EMPTY_BYTES:
                body = b''.join(parts[index:])
                break
            headers.append(chunk.strip(b'\r\n').split(b':', maxsplit=1))

        return cls(f_line, headers=headers, body=body)

    @classmethod
    async def from_reader(cls, reader: StreamReader) -> 'RawHttpMessage':
        """Create a Message from a StreamReader buffer"""
        reader_gen = aiter(reader)
        f_line = await anext(reader_gen)
        headers = []
        async for chunk in reader_gen:
            if chunk == SPACE_BYTES:
                reader.feed_eof()
                break
            headers.append(chunk.strip(b'\r\n').split(b':', maxsplit=1))

        body = b''
        if not reader.at_eof():
            async for chunk in reader:
                body += chunk

        return cls(f_line, headers=headers, body=body)

    async def fill(self, writer: StreamWriter) -> None:
        """Fill writer with self buffer. Does NOT close the writer."""
        # head of message
        writer.write(b'%s%s' % (self._f_line, SPACE_BYTES))
        for header, value in self._headers.items():
            writer.write(b'%s: %s%s' % (header, value, SPACE_BYTES))
        writer.write(SPACE_BYTES)

        await writer.drain()

        # body
        if self._body:
            writer.write(self._body)
            writer.write(EMPTY_BYTES)
            await writer.drain()

    @property
    def info(self):
        """Return the message info."""
        return self._info

    @cached_property
    def raw_bytes(self) -> bytes:
        """Return the raw bytes of message."""
        buffer = bytearray()
        buffer.extend(self._f_line)
        buffer.extend(SPACE_BYTES)
        for header, value in self._headers.items():
            buffer.extend(b'%s: %s%s' % (header, value, SPACE_BYTES))
        buffer.extend(SPACE_BYTES)

        buffer.extend(self._body)

        return buffer

    # header class methods
    def heep_alive(self):
        """Return True if header Connection: keep-alive in headers"""
        return CONNECTION in self._headers and self._headers[CONNECTION] == KEEP_ALIVE

    def add_header(self, header: bytes, value: bytes):
        """Add a header to the message."""
        self._headers[header.strip()] = value.strip()

    def remove_header(self, header_name: bytes):
        """Remove a header from the message.
        Does not raise KeyError if header is not presented."""
        self._headers.pop(header_name.strip(), None)

    def update_header(self, header: bytes, value: bytes):
        """Update a header to the message."""
        self._headers[header.strip()] = value.strip()

    def has_header(self, header_name: bytes):
        """Return True if header exists."""
        return header_name in self._headers

    def get_header_value(self, header_name: bytes):
        """Return value of header"""
        return self._headers.get(header_name, EMPTY_BYTES)
