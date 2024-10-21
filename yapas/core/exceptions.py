from http import HTTPStatus


class DispatchException(Exception):
    """Dispatch Exception"""


class ImproperlyConfigured(DispatchException):
    """Improperly Configured"""


class HTTPException(DispatchException):
    """HTTP Exception"""
    status: HTTPStatus

    def as_bytes(self):
        """Return a bytes representation of the exception"""
        if not self.status:
            return b''
        return b'HTTP/1.1 %d %s\r\n' % (self.status.value, self.status.name.encode())


class UnknownProtocolError(HTTPException):
    """Unknown Protocol"""
    status: HTTPStatus.HTTP_VERSION_NOT_SUPPORTED


class MethodNotAllowed(HTTPException):
    """Method not allowed"""
    status = HTTPStatus.METHOD_NOT_ALLOWED


class BadRequest(HTTPException):
    """Bad Request"""
    status = HTTPStatus.BAD_REQUEST


class NotFoundError(HTTPException):
    """Not Found"""
    status = HTTPStatus.NOT_FOUND


class InternalServerError(HTTPException):
    """Internal Server Error"""
    status = HTTPStatus.INTERNAL_SERVER_ERROR
