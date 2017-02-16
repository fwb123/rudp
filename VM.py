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
                else:
                    # internal message
                    data = b""
                    data += sock.recv(VM_Message.HEADER_SIZE)

                    print(data)

    def __del__(self):
        self.sock.close()
        os.remove("/tmp/RUDP_VM.sock")


if __name__ == "__main__":
    VM = VM()
    VM.ioloop_start()
