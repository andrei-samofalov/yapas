import asyncio

from yapas import conf
from yapas.conf.parser import ConfParser
from yapas.core.constants import WORKING_DIR
from yapas.core.dispatcher import ProxyDispatcher
from yapas.core.server.proxy import ProxyServer
from yapas.core.signals import kill_event


async def main(log_level='debug'):
    server_conf = ConfParser(WORKING_DIR)
    dispatcher = ProxyDispatcher.from_conf(server_conf)
    conf.setup_logging(log_level.upper())
    server = ProxyServer(dispatcher=dispatcher, port=8079, log_level=log_level)
    await server.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        kill_event.set()
