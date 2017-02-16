import unittest
import VN
import struct
import sys
import socket

global instance


class RudpTestCase(unittest.TestCase):
    def setUp(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(('/tmp/VNInterface.sock'))

    def tearDown(self):
        self.sock.close()

    def test_test(self):
        self.assertEquals(2, 2)

    def test_basic(self):
        sock = VN.RUDPSocket()
        self.assertEquals(len(VN.instance.sockets), 1)
        sock.close()
        self.assertEquals(len(VN.instance.sockets), 0)

    def test_bind_passive(self):
        sock = VN.RUDPSocket()
        sock.bind()
        self.assertEquals(len(VN.instance.sockets), 1)
        self.assertEquals(len(VN.instance.bind_table.table), 1)
        sock.close()

        self.assertEquals(len(VN.instance.sockets), 0)
        self.assertEquals(len(VN.instance.bind_table.table), 0)

    def test_bind_active(self):
        btable = VN.instance.bind_table.table

        sock = VN.RUDPSocket()
        sock.bind((8080,))
        self.assertEquals(len(VN.instance.sockets), 1)
        self.assertEquals(len(btable), 1)

        sock2 = VN.RUDPSocket()
        self.assertEquals(len(VN.instance.sockets), 2)

        sock2.bind((1234,))
        self.assertEquals(len(btable), 2)

        self.assertEquals(btable[0].port, 8080)

        self.assertEquals(btable[1].port, 1234)

        sock.close()

        self.assertEquals(len(VN.instance.sockets), 1)
        self.assertEquals(len(btable), 1)
        self.assertEquals(btable[0].port, 1234)

        sock2.close()

        self.assertEquals(len(VN.instance.sockets), 0)
        self.assertEquals(len(btable), 0)


class MessageTestCase(unittest.TestCase):
    def test_defaults(self):
        msg = VN.Message()
        msg.set_default()
        data = msg.pack()
        target = struct.pack("!IIHHIB7s32s5s", 3, 5, 1234, 8080,
                             5, 3, "0" * 7,
                             "aab11697e866e98f548d041a3a553a09", "abcde")
        self.assertEquals(data, target)
        print(msg)

    def test_pack_precondition(self):
        msg = VN.Message()
        with self.assertRaises(AssertionError):
            msg.pack()

    def test_send(self):
        msg = VN.Message()
        msg.set_default()
        addr = VN.Addr("localhost", 9090)
        VN.instance.send(addr, msg)


if __name__ == "__main__":
    options = {
        "local_port": 12345,
        "remote_port": 12346
    }
    if len(sys.argv) > 1:
        options["local_port"] = int(sys.argv[1])
        options["remote_port"] = int(sys.argv[2])
    instance = VN.VN(**options)
    unittest.main()
