import json
from http import HTTPStatus
import signal

from v1.dispatcher import Router
from v1.request import Request
from v1.response import Response


class TestRoute(Router):

    async def get(self, request: Request) -> Response:
        """Get response"""
        return Response(
            status=HTTPStatus.OK,
            headers={},
            body=f'Hello world. Url is {request.url}',
        )

    async def post(self, request: Request) -> Response:
        """Post response"""
        data = request.data()
        reversed_data = {}
        for k, v in data.items():
            reversed_data[v] = k

        return Response(
            status=HTTPStatus.OK,
            headers={"Content-Type": "application/json"},
            body=json.dumps(reversed_data),
        )


class SecondTestRoute(Router):
    async def get(self, request: Request) -> Response:
        1/0
        return Response(
            status=HTTPStatus.OK,
            headers={},
            body=f'You are not prepared!',
        )


class RestartRoute(Router):
    async def get(self, request: Request) -> Response:
        signal.raise_signal(signal.SIGHUP)
        return Response(
            status=HTTPStatus.OK,
            headers={},
            body=f'Restarting...!',
        )
