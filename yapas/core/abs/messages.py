import io
from asyncio import StreamReader, StreamWriter
from functools import cached_property
from typing import Optional, NamedTuple

from yapas.core import exceptions
from yapas.core.abs.enums import MessageType
from yapas.core.constants import EOF_BYTES, SPACE_BYTES, EMPTY_BYTES, CONNECTION, KEEP_ALIVE


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

    @property
    def type(self):
        """Return the message type."""
        return self._info.type

    @property
    def info(self):
        """Return the message info."""
        return self._info

    def heep_alive(self):
        """Return True if header Connection: keep-alive in headers"""
        return CONNECTION in self._headers and self._headers[CONNECTION] == KEEP_ALIVE

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

    async def _prepare_headers(self):
        pass

    async def add_header(self, header: bytes, value: bytes):
        """Add a header to the message."""
        self._headers[header.strip()] = value.strip()

    async def remove_header(self, header_name: bytes):
        """Remove a header from the message.
        Does not raise KeyError if header is not presented."""
        self._headers.pop(header_name.strip(), None)

    async def update_header(self, header: bytes, value: bytes):
        """Update a header to the message."""
        self._headers[header.strip()] = value.strip()

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


class ProxyRequest:
    protocol: bytes
    method: bytes
    url: bytes
    headers: list[tuple[bytes, bytes]]
    body: Optional[bytes] = bytearray()

    accepted_protocols = [b'HTTP/1.1']

    def __init__(self, reader: StreamReader):
        self._reader = reader
        self._raw = bytearray()
        self.headers = []
        self.method = EMPTY_BYTES
        self.url = EMPTY_BYTES
        self.protocol = EMPTY_BYTES

    def __repr__(self):
        return f'{self.method} {self.url} {self.protocol}'

    def __hash__(self):
        # headers?
        return hash(b''.join((self.protocol, self.method, self.url, self.body)))

    @property
    def raw(self) -> bytes:
        """Return raw bytes content of the Request"""
        return self._raw

    async def read_message(self):

        reader = aiter(self._reader)
        f_line = await anext(reader)
        headers = []
        async for chunk in reader:
            if chunk == SPACE_BYTES:
                self._reader.feed_eof()
                break
            headers.append(chunk.strip(b'\r\n').split(b':', maxsplit=1))

        body = b''
        if not self._reader.at_eof():
            async for chunk in reader:
                body += chunk

        return RawHttpMessage(f_line=f_line, headers=headers, body=body)

    def headers_as_str_tuple(self):
        return list(
            map(lambda t_of_bytes: (t_of_bytes[0].decode(), t_of_bytes[1].decode()), self.headers)
        )

    async def _read_status(self):
        if (first_line := await self._reader.readline()) in EOF_BYTES or len(first_line) == 0:
            return
        try:
            self._raw += first_line
            method, path, protocol = first_line.strip().split(b' ')
            print('abstracts:61', method, path, protocol)
        except ValueError:
            raise exceptions.UnknownProtocolError()

        if protocol not in self.accepted_protocols:
            if method in self.accepted_protocols:
                method, protocol = protocol, method
            else:
                raise exceptions.UnknownProtocolError()

        self.protocol = protocol
        self.method = method
        self.url = path  # status

    async def _read_headers(self):
        reader = aiter(self._reader)
        async for data in reader:
            if data in EOF_BYTES:
                self._reader.feed_eof()
                break
            name, _, val = data.strip().partition(b': ')
            # if name == b'Host':
            #     val = b'localhost:8079'
            if name == b'Content-Length':
                print(f'content-length: {val}')
            # if name.lower() == b'connection':
            #     val = b'close'

            self.headers.append((name, val))
            self._raw += b'%s: %s\r\n' % (name, val)

    async def _read_body(self):
        if not self._reader.at_eof():
            self.body += await self._reader.read()
            self._raw += self.body

    async def read_head(self) -> "ProxyRequest":
        await self._read_status()
        await self._read_headers()
        return self

    async def read_body(self) -> "ProxyRequest":
        await self._read_body()
        return self

    async def read(self) -> "ProxyRequest":
        await self.read_head()
        await self.read_body()
        return self

    async def write_gen(self):
        status_line = b'%s %s %s\r\n' % (self.method, self.url, self.protocol)
        yield status_line
        content_length = False
        new_val = len(self.raw)
        print(f'new content-length: {new_val}')
        for header_name, header_value in self.headers:
            print(f'response header {header_name}: {header_value}')
            if header_name.lower() == b'connection':
                header_value = b'close'
            if header_name.lower() == b'content-length':
                header_value = new_val
                content_length = True
            yield b'%s: %s\r\n' % (header_name, header_value)
        if not content_length:
            yield b'Content-Length: %d\r\n' % new_val

        yield SPACE_BYTES
        yield self.body


class ProxyResponse:
    protocol: bytes
    method: bytes
    url: bytes
    headers: list[tuple[bytes, bytes]]
    body: Optional[bytes] = bytearray()

    def __init__(self, writer: StreamWriter):
        self._writer = writer
        self.headers = []
        self.url = b''
        self._raw = bytearray()
        self._file = io.BytesIO()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _write_status(self):
        line = b'HTTP/1.1 200 OK\r\n'
        self._writer.write(
            line
        )
        self._raw += line

    async def _write_headers(self):
        for header, value in self.headers:
            line = b'%s: %s\r\n' % (header, value)
            self._writer.write(line)
            self._raw += line

    async def _write_empty(self):
        self._writer.write(SPACE_BYTES)
        self._raw += SPACE_BYTES

    async def write_head(self):
        await self._write_status()
        await self._write_headers()
        await self._write_empty()
        await self._writer.drain()
        return self

    async def _write_body(self):
        self._writer.write(self.body)
        self._raw += self.body

    async def write_body(self):
        await self._write_body()
        await self._writer.drain()
        return self

    async def write(self, response_bytes: bytes):
        self._writer.write(response_bytes)
        self._raw += response_bytes

        await self._writer.drain()

    async def close(self):
        self._writer.close()
        await self._writer.wait_closed()
