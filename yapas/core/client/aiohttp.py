import aiohttp
from aiohttp.http_writer import HttpVersion

from yapas.core.abs.client import AbstractClient
from yapas.core.abs.messages import RawHttpMessage
from yapas.core.constants import NEWLINE_BYTES


def resolve_version(v: HttpVersion) -> str:
    """Return string representation of HttpVersion."""
    return f'HTTP/{v.major}.{v.minor}'


class AIOHttpClient(AbstractClient):
    """AioHttp based client"""

    async def encode(self, response) -> bytes:
        """Encode proxied response to bytes"""
        # the first status line
        status_line = resolve_version(response.version), response.status, response.reason
        status_line = ' '.join(map(lambda s: str(s), status_line)).encode()
        print(f'{status_line=}')
        # headers
        headers = response.headers
        byte_header_list: list[bytes] = []
        for header in headers.keys():
            h_val = headers.getall(header)
            print(f'header: {header}, len: {len(h_val)}')
            encoded = '; '.join(h_val).encode()

            if header.lower() == 'set-cookie':
                self._expand_cookie, *_ = encoded.split(b';')

            header_tuple = header.encode(), encoded
            # print(f'{header_tuple=}')
            byte_header_list.append(
                b'%s: %s' % header_tuple
            )

        if self._expand_cookie:
            print(f'{self._expand_cookie}')
            byte_header_list.append(b'Cookie: %s' % self._expand_cookie)

        byte_headers = NEWLINE_BYTES.join(byte_header_list)

        # body
        content = await response.read()
        return NEWLINE_BYTES.join((status_line, byte_headers, NEWLINE_BYTES, content))

    async def get_session(self):
        return aiohttp.ClientSession(base_url=self._base_url)

    # todo переделать на message
    async def _raw_request(self, message: RawHttpMessage, method='get') -> bytes:
        """Send Raw proxied request"""
        url = message.info.path.decode()
        async with self.get_session() as session:
            async with session.request(method, url, data=message.raw_bytes) as resp:
                return await self.encode(resp)
