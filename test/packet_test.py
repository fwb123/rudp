import unittest
import contracts
from Packet import Packet


class PacketTestCase(unittest.TestCase):
    def test_set_flags(self):
        p = Packet()
        p.set_flags(Packet.Flags.SYN, Packet.Flags.ACK)
        self.assertEqual(p.flags, Packet.Flags.SYN | Packet.Flags.ACK)

    def test_pack(self):
        p = Packet()
        p.SEQ = 1
        p.ACK = 2
        p.src_port = 8080
        p.dest_port = 9090
        p.set_flags(Packet.Flags.SYN, Packet.Flags.ACK)
        p.set_payload(b"hello")
        target = b'\x00\x00\x00\x01\x00\x00\x00\x02\x1f\x90#\x82\x00\x00\x00\x05\x030000000380d489e62c4e775e665acdda1710bb3hello'
        self.assertEqual(len(p.pack()), len(target))
        self.assertEqual(p.pack(), target)


if __name__ == "__main__":
    unittest.main()
