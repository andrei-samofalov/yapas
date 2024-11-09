import pytest

from yapas.core.abs.messages import _StatusLine, MessageType


@pytest.fixture(scope='module')
def request_bytes():
    return b'GET / HTTP/1.1'


@pytest.fixture(scope='module')
def response_bytes():
    return b'HTTP/1.1 200 OK'


def test_status_line_cls_request(request_bytes):
    line = _StatusLine.from_bytes(request_bytes)
    assert line.status is None
    assert line.reason is None
    assert line.method == b'GET'
    assert line.path == b'/'
    assert line.protocol == b'HTTP/1.1'
    assert line.info.type is MessageType.REQUEST


def test_status_line_cls_response(response_bytes):
    line = _StatusLine.from_bytes(response_bytes)
    assert line.status == b'200'
    assert line.reason == b'OK'
    assert line.method is None
    assert line.path is None
    assert line.protocol == b'HTTP/1.1'
    assert line.info.type is MessageType.RESPONSE

