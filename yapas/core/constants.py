import pathlib
from typing import Final

WORKING_DIR: Final = pathlib.Path(__file__).parent.parent.resolve()

EMPTY_BYTES: Final = b""
NEWLINE_BYTES: Final = b'\r\n'
EOF_BYTES: Final = (EMPTY_BYTES, NEWLINE_BYTES)

OK: Final = b'HTTP/1.1 200 OK'

# headers
CONNECTION: Final = b'Connection'
KEEP_ALIVE: Final = b'keep-alive'

PROXY_FORWARDED_FOR: Final = b'X-Forwarded-For'
HOST: Final = b'Host'
REFERER: Final = b'Referer'
