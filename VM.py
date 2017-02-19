import os
import socket
import logging

import select

from BindTable import BindTable
from VM_Message import VM_Message


class VM(object):
    UDP_PORT = 9191
    MSS = 4096

    def __init__(self):
        self.unix_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.unix_sock.setblocking(0)
        self.unix_sock.bind("/tmp/RUDP_VM.sock")
        self.unix_sock.listen(100)

        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.udp_sock.setblocking(0)
        self.udp_sock.bind(('', self.UDP_PORT))

        self.inputs = [self.unix_sock, self.udp_sock]
        self.outputs = []

        self.read_buffer = {}
        self.write_buffer = {}

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        self.bind_table = BindTable()

    def ioloop_start(self):
        while True:
            readable, writable, exceptional = \
                select.select(self.inputs, self.outputs, self.inputs)
            for sock in readable:
                if sock is self.unix_sock:
                    client, addr = sock.accept()
                    self.logger.info("New connection on unix socket")

                    client.setblocking(0)
                    self.inputs.append(client)
                    self.read_buffer[sock] = ""
                    self.write_buffer[sock] = ""
                elif sock is self.udp_sock:
                    raw, addr = sock.recvfrom(self.MSS)
                    self.logger.debug("New packet on UDP socket\nFrom: {}\nPayload:{}"
                                      .format(addr, raw))
                else:
                    msg = VM.read_message(sock)
                    self.logger.debug("New message on unix socket\n{}".format(msg))
                    self.message_arrived(sock, msg)

    def message_arrived(self, sock : socket.socket, msg : VM_Message):
        action = msg.payload["action"]
        data = msg.payload["data"]
        if action == "is_bindable":
            if self.bind_table.bindable(data):
                out = dict(
                    status=0,
                    message="Ok",
                    data=None
                )
            else:
                out = dict(
                    status=1,
                    message="Not bindable",
                    data=None
                )
            sock.sendall(VM_Message(out))

    @staticmethod
    def read_message(sock: socket.socket) -> VM_Message:
        data = b""
        data += sock.recv(VM_Message.HEADER_SIZE)
        msg = VM_Message.unpack_header(data)
        data += sock.recv(msg.payload_length)
        return VM_Message.unpack(data)

    def __del__(self):
        self.udp_sock.close()
        self.unix_sock.close()
        os.remove("/tmp/RUDP_VM.sock")


if __name__ == "__main__":
    VM = VM()
    VM.ioloop_start()
