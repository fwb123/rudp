import struct
from typing import TypeVar

from contracts import contract
from enum import IntEnum


class VM_Message(object):
    HEADER_SIZE = 5

    class Type(IntEnum):
        READ = 0
        WRITE = 1

    """
    Protocol
    Payload length: 4 bytes
    Type : 1 byte (0 read, 1 write)
    Payload: variable
    """

    def __init__(self):
        self.payload_length = 0
        self.payload = None
        self.type = None

    @contract(type='int,>=0,<=1')
    def set_type(self, type: Type):
        self.type = type

    @contract
    def set_payload(self, payload: str):
        self.payload = payload.encode("utf-8")
        self.payload_length = len(payload)

    def pack(self) -> bytes:
        # precondition
        assert self.payload
        assert self.type
        assert self.payload_length == len(self.payload)
        return struct.pack("!Ib{}s".format(self.payload_length),
                           self.payload_length + self.HEADER_SIZE, self.type, self.payload)

    @staticmethod
    def unpack(raw : bytes) -> 'VM_Message':
        msg = VM_Message()
        tmp = len(raw) - VM_Message.HEADER_SIZE
        msg.payload_length, msg.type, msg.payload = \
            struct.unpack("!Ib{}s".format(tmp), raw)
        msg.payload_length -= VM_Message.HEADER_SIZE
        return msg

    @staticmethod
    def unpack_header(raw : bytes) -> 'VM_Message':
        msg = VM_Message()
        msg.payload_length, msg.type = struct.unpack("!Ib", raw)
        msg.payload_length -= VM_Message.HEADER_SIZE
        return msg

    def __serialize(self) -> str:
        out = ""
        out += "Len:\t\t{}\n".format(self.payload_length)
        out += "Type:\t\t{}\n".format(self.type)
        out += "Payload:\t{}\n".format(self.payload)
        return out


