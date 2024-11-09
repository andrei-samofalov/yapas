class MessageError(Exception):
    pass


class MessageReader:

    def __init__(self, sock, loop):
        self._loop = loop
        self._conn = sock
        self.buffer = b''

    async def get_until(self, what):
        while what not in self.buffer:
            if not await self._fill():
                return b''
        offset = self.buffer.find(what) + len(what)
        data, self.buffer = self.buffer[:offset], self.buffer[offset:]
        return data

    async def get_bytes(self, size):
        while len(self.buffer) < size:
            if not await self._fill():
                return b''
        data, self.buffer = self.buffer[:size], self.buffer[size:]
        return data

    async def _fill(self):
        data = await self._loop.sock_recv(self._conn, 1024)
        if not data:
            if self.buffer:
                raise MessageError('socket closed with incomplete message')
            return False
        self.buffer += data
        return True
