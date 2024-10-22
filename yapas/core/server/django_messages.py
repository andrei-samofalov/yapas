from yapas.core.abs.enums import MessageType
from yapas.core.abs.messages import RawHttpMessage


class DjangoMessage(RawHttpMessage):
    """Implementation for Django csrftoken Cookie"""
    'csrftoken = bls1lQLeouKcoK75fT8VShMlGrvVqt4m'

    @classmethod
    async def from_reader(cls, reader):
        obj = await super().from_reader(reader)
        if not obj.info.type is MessageType.RESPONSE:
            return obj

        if obj.has_header(b'Set-Cookie'):
            value, *_ = obj.get_header_value(b'Set-Cookie').split(b';', maxsplit=1)
            obj.add_header(b'Cookie', value)

        return obj
