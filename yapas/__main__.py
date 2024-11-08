import argparse
import asyncio

from yapas import conf
from yapas.conf.parser import ConfParser
from yapas.core.constants import WORKING_DIR
from yapas.core.dispatcher import ProxyDispatcher
from yapas.core.server.proxy import ProxyServer
from yapas.core.signals import kill_event


async def main(host='0.0.0.0', port=8079, log_level='debug', use_proxy=False):
    server_conf = ConfParser(WORKING_DIR)
    dispatcher = ProxyDispatcher.from_conf(server_conf)

    # just for testing
    if use_proxy is False:
        del dispatcher._locations[b'/*']

    conf.setup_logging(log_level.upper())
    server = ProxyServer(
        dispatcher=dispatcher,
        host=host,
        port=port,
        log_level=log_level
    )
    await server.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0',
                        type=str, help='IP address of the server')
    parser.add_argument('--port', default=8079,
                        type=int, help='Port of the server')
    parser.add_argument('--log_level', default='debug',
                        choices=['debug', 'info', 'warning', 'error'],
                        type=str, help='Logging level')
    parser.add_argument('--use_proxy',
                        action='store_true',
                        help='Whether to use proxy server')
    args: argparse.Namespace = parser.parse_args()

    try:
        asyncio.run(main(**args.__dict__))
    except (KeyboardInterrupt, asyncio.CancelledError):
        kill_event.set()
