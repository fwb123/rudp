import os
import socket

import select
from VM_Message import VM_Message

class VM(object):
    def __init__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.setblocking(0)
        self.sock.bind("/tmp/RUDP_VM.sock")
        self.sock.listen(1)

        self.inputs = [self.sock]
        self.outputs = []

        self.read_buffer = {}
        self.write_buffer = {}


    def ioloop_start(self):
        while True:
            readable, writable, exceptional = \
                select.select(self.inputs, self.outputs, self.inputs)
            for sock in readable:
                if sock is self.sock:
                    # new internal connection
                    client, addr = sock.accept()
                    print("New connection from", addr)

                    client.setblocking(0)
                    self.inputs.append(client)
                    self.read_buffer[sock] = ""
                    self.write_buffer[sock] = ""

                else:
                    # internal message
                    msg = VM.read_message(sock)
                    if msg.type == VM_Message.Type.WRITE:
                        self.write_buffer[sock] += msg.payload
                    elif:
                        msg.type == VM_Message.Type.READ:


    @staticmethod
    def read_message(sock : socket.socket) -> VM_Message:
        data = b""
        data += sock.recv(VM_Message.HEADER_SIZE)
        msg = VM_Message.unpack_header(data)
        data += sock.recv(msg.payload_length)
        return VM_Message.unpack(data)



    def __del__(self):
        self.sock.close()
        os.remove("/tmp/RUDP_VM.sock")


if __name__ == "__main__":
    VM = VM()
    VM.ioloop_start()
