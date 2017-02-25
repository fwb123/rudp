import hashlib
import struct


class Packet:
    """
        Protocol
        SEQ: 4 bytes
        ACK: 4 bytes
        Source port: 2 bytes
        Destination port: 2 bytes
        Payload length: 4 bytes
        FLAGS : 1 byte
        misc : 7 bytes
        checksum: 32 bytes
        payload : variable
        _______________________

        header size : 36
        packet size : header size + payload length

         ---------------------------------------------------------------
        |		  SEQ (4 bytes)			|			ACK (4 bytes)		|
        |---------------------------------------------------------------|
        |  Source port	 |  Dest port	|	Payload length (4 bytes)	|
        |---------------------------------------------------------------|
        | FLAGS  |					Misc (7 bytes)                      |
        |---------------------------------------------------------------|
        |						Checksum (32 bytes)						|
        |																|
        |																|
        |---------------------------------------------------------------|
        |						Payload (variable)						|
         ---------------------------------------------------------------

    """
    HEADER_SIZE = 56

    class Flags:
        SYN = (1 << 0)
        ACK = (1 << 1)
        RST = (1 << 2)
        SYN_ACK = SYN | ACK

        @staticmethod
        def get(flag):
            dic = {
                "1": "SYN",
                "2": "ACK",
                "4": "RST",
                "3": "SYN_ACK"
            }
            return dic[str(flag)]

    def __init__(self):
        self.SEQ = -1
        self.ACK = -1
        self.src_port = -1
        self.dest_port = -1
        self.payload_length = 0
        self.flags = -1
        self.misc = b"0" * 7
        self.checksum = b"0" * 32
        self.payload = b""

    def set_default(self):
        self.SEQ = 3
        self.ACK = 5
        self.src_port = 1234
        self.dest_port = 8080
        self.payload_length = 5
        self.flags = self.Flags.SYN | self.Flags.ACK
        self.misc = "0" * 7
        self.payload = "abcde"

    def pack(self) -> bytes:
        # preconditions
        assert self.SEQ != -1
        assert self.ACK != -1
        assert self.src_port != -1
        assert self.dest_port != -1
        assert self.flags > 0

        assert len(self.payload) == self.payload_length

        self.checksum = b"0" * 32

        self.checksum = self.compute_checksum(self)

        data = struct.pack("!IIHHIB7s32s{}s".format(self.payload_length),
                           self.SEQ, self.ACK, self.src_port,
                           self.dest_port, self.payload_length,
                           self.flags, self.misc, self.checksum,
                           self.payload)

        return data

    @staticmethod
    def compute_checksum(msg: 'Packet') -> bytes:
        data = struct.pack("!IIHHIB7s32s%ss" % msg.payload_length,
                           msg.SEQ, msg.ACK, msg.src_port,
                           msg.dest_port, msg.payload_length,
                           msg.flags, msg.misc, msg.checksum,
                           msg.payload)

        r = hashlib.md5(data).hexdigest().encode("utf-8")
        assert len(r) == 32
        return r

    @staticmethod
    def unpack(raw: bytes) -> 'Packet':
        msg = Packet()
        (msg.SEQ, msg.ACK, msg.src_port,
         msg.dest_port, msg.payload_length,
         msg.flags, msg.misc, msg.checksum,
         ) = struct.unpack("!IIHHIB7s32s", raw[:Packet.HEADER_SIZE])
        msg.payload = raw[Packet.HEADER_SIZE:]

        assert msg.payload_length == len(msg.payload)
        checksum = msg.checksum
        msg.checksum = b"0" * 32
        assert checksum == Packet.compute_checksum(msg)
        msg.checksum = checksum
        return msg

    def set_payload(self, payload: bytes):
        self.payload_length = len(payload)
        self.payload = payload

    def set_flags(self, *flags):
        self.flags = 0
        for flag in flags:
            self.flags |= flag

    def __str__(self):
        out = """
SEQ:\t\t{}
ACK:\t\t{}
Src port:\t{}
Dest port:\t{}
Payload len:\t{}
Flags:\t\t{}
Checksum:\t{}
Payload:\t{}
			""".format(self.SEQ, self.ACK, self.src_port, self.dest_port,
                       self.payload_length, self.Flags.get(self.flags), self.checksum,
                       self.payload)
        return out
