import unittest
import contracts

from VM_Message import VM_Message


class MessageTestCase(unittest.TestCase):
    def test_set_payload(self):
        msg = VM_Message()
        msg.set_payload({"test": "first"})
        target = dict(test="first")
        self.assertEqual(msg.payload, target)

    def test_set_payload_init(self):
        msg = VM_Message({"test": "first"})
        target = dict(test="first")
        self.assertEqual(msg.payload, target)

    def test_pack_precondition(self):
        msg = VM_Message()
        with self.assertRaises(AssertionError):
            msg.pack()

    def test_set_payload_int(self):
        msg = VM_Message()
        with self.assertRaises(contracts.interface.ContractNotRespected):
            msg.set_payload(4)

    def test_set_payload_none(self):
        msg = VM_Message()
        with self.assertRaises(contracts.interface.ContractNotRespected):
            msg.set_payload(None)

    def test_pack(self):
        msg = VM_Message()
        msg.set_payload({"data": "hello"})
        data = msg.pack()
        target = b'\x00\x00\x00\x15{"data": "hello"}'
        self.assertEqual(data, target)

    def test_unpack(self):
        raw = b'\x00\x00\x00\x15{"data": "hello"}'
        msg = VM_Message.unpack(raw)
        self.assertEqual(msg.payload, {"data": "hello"})
        self.assertEqual(msg.payload_length, 17)

    def test_unpack_header(self):
        raw = b'\x00\x00\x00\x15'
        msg = VM_Message.unpack_header(raw)
        self.assertEqual(msg.payload_length, 17)


if __name__ == "__main__":
    unittest.main()
