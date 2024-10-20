from http import HTTPStatus


class DispatchException(Exception):
    """Dispatch Exception"""


class ImproperlyConfigured(DispatchException):
    """Improperly Configured"""


class HTTPException(DispatchException):
    """HTTP Exception"""
    status: HTTPStatus

    def __bytes__(self):
        if not self.status:
            return b''
        return (
            b'HTTP/1.1 %d %s\r\n\r\n' % (self.status.value, self.status.name.encode())
        )


class MethodNotAllowed(HTTPException):
    """Method not allowed"""
    status = HTTPStatus.METHOD_NOT_ALLOWED


class BadRequest(HTTPException):
    """Bad Request"""
    status = HTTPStatus.BAD_REQUEST


class NotFoundError(HTTPException):
    """Not Found"""
    status = HTTPStatus.NOT_FOUND
