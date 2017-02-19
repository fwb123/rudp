import json
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
    Payload: variable
    -----------------------------------------------------------------
    |	  payload_length (4 bytes) |		Payload (varialbe)		|
    -----------------------------------------------------------------

    """

    HEADER_SIZE = 4

    @contract
    def __init__(self, payload : dict = {}):
        self.payload_length = 0
        self.payload = payload
        self.nbytes = 0

    @contract
    def set_payload(self, payload: dict):
        self.payload = payload
        self.payload_length = len(json.dumps(self.payload).encode("utf-8"))

    def pack(self) -> bytes:
        # precondition
        assert self.payload
        assert self.payload_length == len(json.dumps(self.payload).encode("utf-8"))

        payload = json.dumps(self.payload).encode("utf-8")
        return struct.pack("!I{}s".format(self.payload_length),
                           self.payload_length + self.HEADER_SIZE, payload)

    @staticmethod
    def unpack(raw: bytes) -> 'VM_Message':
        msg = VM_Message()
        payload_length = len(raw) - VM_Message.HEADER_SIZE
        msg.payload_length, msg.payload = \
            struct.unpack("!I{}s".format(payload_length), raw)

        msg.payload = json.loads(msg.payload.decode("utf-8"))
        msg.payload_length -= VM_Message.HEADER_SIZE

        # print(raw, msg.payload_length, payload_length)
        assert msg.payload_length == payload_length
        return msg

    @staticmethod
    def unpack_header(raw: bytes) -> 'VM_Message':
        # precondition
        assert len(raw) == VM_Message.HEADER_SIZE

        msg = VM_Message()
        msg.payload_length, = struct.unpack("!I", raw)
        msg.payload_length -= VM_Message.HEADER_SIZE
        return msg

    def __str__(self) -> str:
        payload = json.dumps(self.payload, indent=4, sort_keys=True)
        out = ""
        out += "Len:\t\t{}\n".format(self.payload_length)
        out += "Payload:\t{}\n".format(payload)
        return out
