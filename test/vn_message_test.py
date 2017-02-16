import unittest
import struct
import sys

sys.path.append('../')

import contracts
from VM_Message import VM_Message


class MessageTestCase(unittest.TestCase):
    def test_pack_precondition(self):
        msg = VM_Message()
        with self.assertRaises(AssertionError):
            msg.pack()

    def test_read(self):
        msg = VM_Message()
        msg.set_type(VM_Message.Type.READ)
        self.assertEqual(int(msg.type), 0)

    def test_write(self):
        msg = VM_Message()
        msg.set_type(VM_Message.Type.WRITE)
        self.assertEqual(msg.type, 1)

    def test_type(self):
        msg = VM_Message()
        with self.assertRaises(contracts.interface.ContractNotRespected):
            msg.set_type(5)

    def test_set_payload(self):
        msg = VM_Message()
        with self.assertRaises(contracts.interface.ContractNotRespected):
            msg.set_payload(4)


    def test_set_payload_none(self):
        msg = VM_Message()
        with self.assertRaises(contracts.interface.ContractNotRespected):
            msg.set_payload(None)



    def test_pack(self):
        msg = VM_Message()
        msg.set_type(VM_Message.Type.WRITE)
        msg.set_payload("hello")
        print(msg.payload)
        data = msg.pack()
        target = b'\x00\x00\x00\n\x01hello'
        self.assertEqual(data, target)

    def test_unpack(self):
        raw = b'\x00\x00\x00\n\x01hello'
        msg = VM_Message.unpack(raw)
        self.assertEqual(msg.payload_length, 5)
        self.assertEqual(msg.type, VM_Message.Type.WRITE)
        self.assertEqual(msg.payload, b"hello")

    def test_unpack_header(self):
        raw = b'\x00\x00\x00\n\x01'
        msg = VM_Message.unpack_header(raw)
        self.assertEqual(msg.payload_length, 5)
        self.assertEqual(msg.type, VM_Message.Type.WRITE)



if __name__ == "__main__":
    unittest.main()
