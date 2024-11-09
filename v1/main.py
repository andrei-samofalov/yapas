import argparse
import asyncio
import importlib
from typing import NoReturn, Optional

from app.routes import TestRoute, SecondTestRoute, RestartRoute
from yapas import conf
from yapas.core.constants import WORKING_DIR
from v1.dispatcher import Dispatcher, Router
from v1.asgi_server import ASGIServer
from yapas.core.signals import kill_event

local = True


async def main(
    *,
    app: str,
    host: str = '0.0.0.0',
    port: int = 8079,
    static_path: Optional[str] = None,
    log_level: Optional[str] = 'debug',
) -> NoReturn:
    """Start async server with configured params:

    :param app: application import path
    :param host: IP address of the server
    :param port: Port of the server
    :param static_path: Path to the static folder
    :param log_level: Logging level
    """

    try:
        path, app_name = app.split(":")
        if not local:
            app_path = f"{WORKING_DIR}/{path.replace('.', '/')}"
        else:
            app_path = path.replace('.', '/')
        str_path = str(app_path).replace('/', '.')
        module = importlib.import_module(str_path)
        app = getattr(module, app_name)

    except (AttributeError, ModuleNotFoundError, ImportError) as exc:
        print(exc)
        exit("app can not be found")

    conf.setup_logging(log_level.upper())

    dispatcher = Dispatcher()
    root = Router()
    dispatcher.register_root(root)

    first_route = TestRoute()
    second_route = SecondTestRoute()
    # third_route = TestRoute()
    restart_route = RestartRoute()

    root.register_router('/testme', first_route)  # get/post
    root.register_router('/test', second_route)  # internal server error
    root.register_router('/restart', restart_route)  # sending SIGHUP signal
    # root.register_router('/test', third_route)  # test exception on startup

    await dispatcher.perform_checks()

    server = ASGIServer(host=host, port=port, app=app, dispatcher=dispatcher)
    if static_path:
        server.add_static_path(static_path)

    await server.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--app',
                        default='yapas.asgi:app', type=str,
                        help='An application or an application factory. '
                             'Should be passed if following format: '
                             '<path/to/module>:<app_object>')
    parser.add_argument('--host', default='0.0.0.0',
                        type=str, help='IP address of the server')
    parser.add_argument('--port', default=8079,
                        type=int, help='Port of the server')
    parser.add_argument('--static_path', default='static',
                        type=str, help='Path to the static folder')
    parser.add_argument('--log_level', default='debug',
                        choices=['debug', 'info', 'warning', 'error'],
                        type=str, help='Logging level')

    args: argparse.Namespace = parser.parse_args()

    try:
        asyncio.run(main(**args.__dict__))  # noqa
    except KeyboardInterrupt:
        kill_event.set()
