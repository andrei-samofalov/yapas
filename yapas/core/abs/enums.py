from enum import Enum, auto


class MessageType(Enum):
    """Type of RawMessage"""
    RESPONSE = auto()
    REQUEST = auto()
