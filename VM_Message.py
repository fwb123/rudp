import struct
from contracts import contract
from enum import IntEnum


class VM_Message(object):
    """
    Internal message for communication between virtual transport layer and application
    For write it pushes message payload into buffer for sending data over network
    For read it tries to read data from the buffer

    Protocol
    Payload length: 4 bytes
    Type : 1 byte (0 read, 1 write)
    Bytes to read/write: 4 bytes
    Payload: variable
    -----------------------------------------------------------------
    |	  payload_length (4 bytes) |			ACK (4 bytes)		|
    |---------------------------------------------------------------|
    |  Source port	 |  Dest port	|	Payload length (4 bytes)	|
    |---------------------------------------------------------------|
    | FLAGS  |					Misc (7 bytes)                      |
    |---------------------------------------------------------------|
    |						Payload (variable)						|
    -----------------------------------------------------------------

    """

    HEADER_SIZE = 5

    class Type(IntEnum):
        READ = 0
        WRITE = 1

    def __init__(self):
        self.payload_length = 0
        self.payload = None
        self.type = None
        self.nbytes = 0

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
    def unpack(raw: bytes) -> 'VM_Message':
        msg = VM_Message()
        tmp = len(raw) - VM_Message.HEADER_SIZE
        msg.payload_length, msg.type, msg.payload = \
            struct.unpack("!Ib{}s".format(tmp), raw)
        msg.payload_length -= VM_Message.HEADER_SIZE
        return msg

    @staticmethod
    def unpack_header(raw: bytes) -> 'VM_Message':
        msg = VM_Message()
        msg.payload_length, msg.type = struct.unpack("!Ib", raw)
        msg.payload_length -= VM_Message.HEADER_SIZE
        return msg

    def __str__(self) -> str:
        out = ""
        out += "Len:\t\t{}\n".format(self.payload_length)
        out += "Type:\t\t{}\n".format(self.type)
        out += "Payload:\t{}\n".format(self.payload)
        return out
