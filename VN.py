import socket
import uuid
import struct
import sys
import random
import time
import threading
import select
import os
import json

from Packet import Packet
from Addr import Addr
from BindContext import BindContext
from BindTable import BindTable


class VN:
    MSS = 2 ** 15

    def __init__(self, local_port, remote_port):
        print("Running VN")
        self.local_port = local_port
        self.remote_port = remote_port

        self.bind_table = BindTable()
        self.sockets = {}  # dict: <id : socket>

    def bindable(self, context):
        # precondition
        assert isinstance(context, BindContext)
        return self.bind_table.bindable(context)

    def bind(self, context):
        assert isinstance(context, BindContext)

        self.bind_table.insert(context)

    def add_socket(self, sock):
        # precondition
        assert isinstance(sock, RUDPSocket)
        self.sockets[sock.sock_id] = sock

    def remove_socket(self, sock):
        # precondition
        assert isinstance(sock, RUDPSocket)

        del self.sockets[sock.sock_id]
        for i, item in enumerate(self.bind_table.table):
            if item.sock_id == sock.sock_id:
                del self.bind_table.table[i]

    def send(self, addr, msg):
        # precondition
        assert isinstance(addr, Addr)
        assert isinstance(msg, Message)

        msg.dest_port = addr.port
        data = msg.pack()
        self.socket.sendto(data, (addr.ip, self.remote_port))

    def _packet_arrived(self, pkt, addr):
        # precondition
        assert isinstance(addr, Addr)
        assert isinstance(pkt, Packet)

        print("Packed arrived:")
        print(addr)
        print(msg)


class VNInterface:

    def __init__(self, vn):
        self.vn = vn
        self.unix_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.unix_sock.setblocking(0)
        self.unix_sock.bind("/tmp/VNInterface.sock")
        self.unix_sock.listen(5)

        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind(('', vn.local_port))

        self.inputs = [self.unix_sock, self.udp_sock]
        self.outputs = []

    def ioloop_start(self):
        while True:
            readable, writable, exceptional = \
                select.select(self.inputs, self.outputs, self.inputs)
            for sock in readable:
                if sock is self.unix_sock:
                    # new internal connection
                    client, addr = sock.accept()
                    print("New connection from")
                    print(addr)
                    client.setblocking(0)
                    self.inputs.append(client)
                elif sock is self.udp_sock:
                    # external udp message
                    raw, addr = sock.recvfrom(VN.MSS)
                    self.vn._packet_arrived(raw, addr)
                else:
                    # internal message
                    raw = ""
                    data = sock.recv(4)
                    print(len(data))
                    assert len(data) == 4
                    raw += data
                    payload_length, = struct.unpack("!I", data)
                    data = sock.recv(payload_length)
                    raw += data
                    msg = self.Message.unpack(raw)
                    print(msg)
                    # print(locals())
                    res = getattr(self, msg.payload)()
                    res = json.dumps(res)
                    out = struct.pack("!I{}s".format(len(res)),
                                      len(res), res)
                    sock.sendall(out)

    def socket_count(self):
        return len(self.vn.sockets)

    def __del__(self):
        self.unix_sock.close()
        os.remove("/tmp/VNInterface.sock")


if __name__ == "__main__":
    options = {
        "local_port": 12345,
        "remote_port": 12346
    }

    if len(sys.argv) > 1:
        options["local_port"] = int(sys.argv[1])
        options["remote_port"] = int(sys.argv[2])

    instance = VN(**options)
    VNiface = VNInterface(instance)
    VNiface.ioloop_start()

    # instance.ioloop_start()
    # time.sleep(5)
    # for i in range(100):
    # print("stoooooop")
    # instance.ioloop_stop()
