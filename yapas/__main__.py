import argparse
import asyncio
from typing import NoReturn, Optional

from yapas import conf
from yapas.app.routes import TestRoute, SecondTestRoute, RestartRoute
from yapas.core.dispatcher import Dispatcher, Router
from yapas.core.server import Server, kill_event


async def main(
    *,
    host: str = '0.0.0.0',
    port: int = 8079,
    static_path: Optional[str] = None,
    log_level: Optional[str] = 'debug',
) -> NoReturn:
    """Start async server with configured params:

    :param host: IP address of the server
    :param port: Port of the server
    :param static_path: Path to the static folder
    :param log_level: Logging level
    """
    conf.setup_logging(log_level.upper())

    dispatcher = Dispatcher()
    root = Router(dispatcher)

    first_route = TestRoute()
    second_route = SecondTestRoute()
    # third_route = TestRoute()
    restart_route = RestartRoute()

    root.register_router('/testme', first_route)  # get/post
    root.register_router('/test', second_route)  # internal server error
    root.register_router('/restart', restart_route)  # sending SIGHUP signal
    # root.register_router('/test', third_route)  # test exception on startup

    dispatcher.register_root(root)

    await dispatcher.perform_checks()

    server = Server(host=host, port=port, dispatcher=dispatcher)
    if static_path:
        server.add_static_path(static_path)

    await server.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0',
                        type=str, help='IP address of the server')
    parser.add_argument('--port', default=8079,
                        type=int, help='Port of the server')
    parser.add_argument('--static_path', default=None,
                        type=str, help='Path to the static folder')
    parser.add_argument('--log_level', default='debug',
                        choices=['debug', 'info', 'warning', 'error'],
                        type=str, help='Logging level')

    args: argparse.Namespace = parser.parse_args()

    try:
        asyncio.run(main(**args.__dict__))  # noqa
    except KeyboardInterrupt:
        kill_event.set()
