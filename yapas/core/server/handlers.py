import pathlib
import signal
from logging import getLogger

from cachetools import TTLCache

from yapas.core.constants import NOT_FOUND, OK, INTERNAL_ERROR
from yapas.core.abs.messages import RawHttpMessage
from yapas.core.client.socket import SocketClient
from yapas.core.statics import async_open, render_base

logger = getLogger(__name__)

cache = TTLCache(maxsize=300, ttl=60)

files = 0


async def proxy(message: RawHttpMessage) -> RawHttpMessage:
    """Proxy handler"""
    _client = SocketClient()
    return await _client.raw(message)


# async def _proxy(message: RawHttpMessage) -> RawHttpMessage:
#     """Handler for proxied requests"""
#     import asyncio
#     from yapas.conf.constants import EMPTY_BYTES, SPACE_BYTES
#     global files
#     files += 1
#     reader, writer = await asyncio.open_connection('0.0.0.0', 8000)
#
#     print(f"request {request.raw=}")
#     gen = request.write_gen()
#     status = await anext(gen)
#     writer.write(status)
#     async for header in gen:
#         writer.write(header)
#         if header == SPACE_BYTES:
#             break
#
#     await writer.drain()
#
#     async for body_line in gen:
#         writer.write(body_line)
#
#     # writer.write(request.raw)
#     await writer.drain()
#
#     response = bytearray()
#
#     try:
#         reader_aiter = aiter(reader)
#         f_line = await anext(reader_aiter)
#         print(f"{f_line=}")
#         async for chunk in reader_aiter:
#             response.extend(chunk)
#             if chunk == EMPTY_BYTES:
#                 break
#             print(f"Received chunk: {chunk}")
#
#     except Exception as e:
#         print(f"Error reading response: {e}")
#     finally:
#         writer.close()
#         await writer.wait_closed()
#
#     # resp = ProxyRequest(reader)
#     # await resp.read()
#     # data = bytearray()
#     # async for line in reader:
#     #     print(f"{line=}")
#     #     if reader.at_eof():
#     #         break
#     #     data += line
#     #
#     # print(f'data read, sending {files}')
#     # writer.close()
#     # await writer.wait_closed()
#     return response

# return await client.raw(request, request.method.decode())


async def static(message: RawHttpMessage) -> RawHttpMessage:
    """Static files handler, uses TTLCache."""

    # todo переписать на нормальный хендлер сервера
    path = message.info.path.decode().removeprefix('/static')
    static_path = f'/var/www/static/ma-tool{path}'

    if "?" in static_path:
        # versioned static files
        static_path, *_ = static_path.split("?")

    if (result := cache.get(static_path)) is not None:
        return result

    if not pathlib.Path(static_path).exists():
        return RawHttpMessage(NOT_FOUND)  # todo abs

    try:
        async with async_open(static_path) as f:
            return RawHttpMessage(OK, body=await f.read())
    except Exception as e:
        logger.exception(e)
        return RawHttpMessage(INTERNAL_ERROR)


async def not_found(message: RawHttpMessage) -> 'RawHttpMessage':
    """Not found handler"""
    template = await render_base(
        error_msg=f"Page {message.info.path.strip().decode()} not found on this server"
    )
    return RawHttpMessage(OK, body=template)


async def restart(_message: RawHttpMessage):
    """Restart handler"""
    signal.raise_signal(signal.SIGHUP)
    template = await render_base(error_msg=f"Restarting...")
    return RawHttpMessage(OK, body=template)
