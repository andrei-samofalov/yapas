import pathlib
from typing import Final

WORKING_DIR: Final = pathlib.Path(__file__).parent.parent.resolve()

EMPTY_BYTES: Final = b""
SPACE_BYTES: Final = b'\r\n'
EOF_BYTES: Final = (EMPTY_BYTES, SPACE_BYTES)

OK = b'HTTP/1.1 200 OK'
NOT_FOUND = b'HTTP/1.1 404 NOT_FOUND'
INTERNAL_ERROR = b'HTTP/1.1 500 INTERNAL ERROR'


# headers
CONNECTION = b'Connection'
KEEP_ALIVE = b'keep-alive'
