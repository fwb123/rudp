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

    def __init__(self):
        self.SEQ = -1
        self.ACK = -1
        self.src_port = -1
        self.dest_port = -1
        self.payload_length = -1
        self.FLAGS = -1
        self.misc = "0" * 7
        self.checksum = "0" * 32
        self.payload = None

    def set_default(self):
        self.SEQ = 3
        self.ACK = 5
        self.src_port = 1234
        self.dest_port = 8080
        self.payload_length = 5
        self.FLAGS = self.Flags.SYN | self.Flags.ACK
        self.misc = "0" * 7
        self.payload = "abcde"

    def pack(self):
        # preconditions
        assert self.SEQ != -1
        assert self.ACK != -1
        assert self.src_port != -1
        assert self.dest_port != -1
        assert self.payload_length != -1
        assert self.FLAGS != -1
        assert self.payload != None
        assert len(self.payload) == self.payload_length

        self.checksum = "0" * 32

        self.checksum = self.compute_checksum(self)

        data = struct.pack("!IIHHIB7s32s%ss" % self.payload_length,
                           self.SEQ, self.ACK, self.src_port,
                           self.dest_port, self.payload_length,
                           self.FLAGS, self.misc, self.checksum,
                           self.payload)

        return data

    @staticmethod
    def compute_checksum(msg: 'Packet'):
        data = struct.pack("!IIHHIB7s32s%ss" % msg.payload_length,
                           msg.SEQ, msg.ACK, msg.src_port,
                           msg.dest_port, msg.payload_length,
                           msg.FLAGS, msg.misc, msg.checksum,
                           msg.payload)
        return hashlib.md5(data).hexdigest()

    @staticmethod
    def unpack(raw: 'Packet'):
        msg = Packet()
        (msg.SEQ, msg.ACK, msg.src_port,
         msg.dest_port, msg.payload_length,
         msg.FLAGS, msg.misc, msg.checksum,
         ) = struct.unpack("!IIHHIB7s32s", raw[:Packet.HEADER_SIZE])
        msg.payload = raw[Packet.HEADER_SIZE:]

        assert msg.payload_length == len(msg.payload)
        checksum = msg.checksum
        msg.checksum = "0" * 32
        assert checksum == self.compute_checksum(msg)
        msg.checksum = checksum
        return msg

    def set_payload(self, payload):
        self.payload_length = len(payload)
        self.payload = payload

    def __str__(self):
        out = """
SEQ:\t\t{}
ACK:\t\t{}
Src port:\t{}
Dest port:\t{}
Payload len:\t{}
FLAGS:\t\t{}
Checksum:\t{}
Payload:\t{}
			""".format(self.SEQ, self.ACK, self.src_port, self.dest_port,
                       self.payload_length, self.FLAGS, self.checksum,
                       self.payload)
        return out
