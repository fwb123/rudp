import copy
import os
import socket
import logging

import select

from enum import *
from queue import Queue
from threading import Thread

from contracts import contract

from BindTable import BindTable
from ConnectionTable import ConnectionTable
from Packet import Packet
from VM_Message import VM_Message


class States(IntEnum):
    CLOSED = 0
    LISTENING = 1
    SYN_SENT = 2
    SYN_RCVD = 3
    ESTABLISHED = 4
    FIN_WAIT_1 = 5
    FIN_WAIT_2 = 6
    CLOSING = 7
    CLOSE_WAIT = 8
    TIME_WAIT = 9
    LAST_ACK = 10


class VM(object):
    """

    TODO:
    Remove socket from bindtable on close
    """
    UDP_PORT = 9191
    MSS = 4096

    def __init__(self):
        self.running = False
        self.unix_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.unix_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.unix_sock.setblocking(0)
        try:
            self.unix_sock.bind("/tmp/RUDP_VM.sock")
        except OSError:
            os.remove("/tmp/RUDP_VM.sock")
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
        self.packet_queue = Queue()  # <packet, addr>
        self.accept_queue = Queue()  # <unix_sock, internal_socket>

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        self.bind_table = BindTable()
        self.connection_table = ConnectionTable()

        self.socket_container = InternalSocketContainer()

    def packet_dispatcher(self):
        while self.running:
            item = self.packet_queue.get()
            self.udp_sock.sendto(item[0].pack(), item[1])
            self.packet_queue.task_done()

    def accept_dispatcher(self):
        while self.running:
            unix_sock, internal_sock = self.accept_queue.get()
            sock = self.socket_container.get_undelivered(internal_sock.b_context[1])
            if sock:
                sock.delivered = True
                out = dict(
                    status=0,
                    message="Ok",
                    data=(sock.remote_addr,)
                )
                unix_sock.sendall(VM_Message(out).pack())
            self.accept_queue.task_done()
            if not sock:
                self.accept_queue.put((unix_sock, internal_sock))

    @contract
    def push_packet(self, packet: Packet, addr: tuple):
        self.packet_queue.put((packet, addr))

    def ioloop_start(self):
        self.running = True
        t = Thread(target=self.packet_dispatcher)
        t.start()

        t1 = Thread(target=self.accept_dispatcher)
        t1.start()
        while True:
            readable, writable, exceptional = \
                select.select(self.inputs, self.outputs, self.inputs)
            for sock in readable:
                if sock is self.unix_sock:
                    client, addr = sock.accept()
                    self.logger.info("New connection on unix socket")
                    client.setblocking(0)
                    self.inputs.append(client)
                elif sock is self.udp_sock:
                    p, addr = VM.read_packet(sock)
                    # self.logger.debug("New packet on UDP socket\nFrom: {}\nPayload:{}"
                    #                   .format(addr, p))
                    self.packet_arrived(p, addr)

                else:
                    try:
                        msg = VM.read_message(sock)
                    except EOFError as e:
                        self.logger.debug(str(e))
                        self.inputs.remove(sock)
                        tmp = self.socket_container.get_by_unix_sock(sock)
                        self.socket_container.forget(tmp)
                        self.logger.debug("Disconnect on unix socket")
                        continue

                    self.logger.debug("New message on unix socket\n{}".format(msg))
                    self.message_arrived(sock, msg)

    @contract(addr='tuple[2]')
    def packet_arrived(self, p: Packet, addr: tuple):  # addr <ip, port>
        self.logger.debug("Packet arrived from{}\n{}".format(addr, p))
        port = p.dest_port
        try:
            internal_sock = self.socket_container.get_by_port(port)
        except ValueError:
            self.logger.error("Socket not found in bind table")
            p.src_port, p.dest_port = p.dest_port, p.src_port
            p.set_flags(Packet.Flags.RST)
            self.push_packet(p, addr)
            return

        flags = p.flags
        if flags == Packet.Flags.SYN:
            if internal_sock.state != States.LISTENING:
                # socket is not in listening state
                p.src_port, p.dest_port = p.dest_port, p.src_port
                p.set_flags(Packet.Flags.RST)
                self.push_packet(p, addr)
                self.logger.debug("Socket is not listening")
                return
            elif self.socket_container.count_zombies(internal_sock.b_context[1]) > internal_sock.listen:
                p.src_port, p.dest_port = p.dest_port, p.src_port
                p.set_flags(Packet.Flags.RST)
                self.push_packet(p, addr)
                self.logger.debug("Socket backlog is full")
                return
            else:
                spawned_sock = copy.copy(internal_sock)
                spawned_sock.state = States.SYN_RCVD
                spawned_sock.remote_addr = addr[0], p.src_port
                self.socket_container.insert(spawned_sock)
                self.connection_table.zombies.append(spawned_sock)
                p.src_port, p.dest_port = p.dest_port, p.src_port
                p.set_flags(p.Flags.SYN_ACK)
                self.push_packet(p, addr)

        elif flags == Packet.Flags.SYN_ACK:
            if internal_sock.state != States.SYN_SENT:
                self.logger.debug("Socket did initiate connection")
                return
            else:
                internal_sock.state = States.ESTABLISHED
                internal_sock.remote_addr = addr[0], p.src_port
                p.src_port, p.dest_port = p.dest_port, p.src_port
                p.set_flags(p.Flags.ACK)
                self.push_packet(p, addr)
                out = dict(
                    status=0,
                    message="Ok",
                    data=None
                )
                internal_sock.unix_sock.sendall(VM_Message(out).pack())

        elif flags == Packet.Flags.ACK:
            internal_sock = self.socket_container.get_by_connection(port, (addr[0], p.src_port))
            internal_sock.state = States.ESTABLISHED
            return
        elif flags == Packet.Flags.RST:
            out = dict(
                status=1,
                message="Reset",
                data=None
            )
            internal_sock.unix_sock.sendall(VM_Message(out).pack())

        else:
            self.logger.error("Unrecognized flags")

    @contract
    def message_arrived(self, sock: socket.socket, msg: VM_Message):
        action = msg.payload["action"]
        data = tuple(msg.payload["data"])
        if action == "is_bindable":
            if self.socket_container.bindable(data):
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
            sock.sendall(VM_Message(out).pack())

        elif action == "bind":
            try:
                curr = InternalSocket(sock, data)
                self.socket_container.insert(curr)
                out = dict(
                    status=0,
                    message="Ok",
                    data=None
                )
            except ValueError as e:
                out = dict(
                    status=1,
                    message=str(e),
                    data=None
                )
            except:
                raise RuntimeError("Exception not caught")

            sock.sendall(VM_Message(out).pack())

        elif action == "connect":
            try:
                internal_sock = self.socket_container.get_by_unix_sock(sock)
            except ValueError:
                self.logger.error("Socket not found in bind table")
                return
            p = Packet()
            p.SEQ = 1
            p.ACK = 0
            p.set_flags(Packet.Flags.SYN)
            p.src_port = internal_sock.b_context[1]
            p.dest_port = data[1]
            dest_ip = data[0]
            internal_sock.state = States.SYN_SENT
            self.push_packet(p, (dest_ip, VM.UDP_PORT))

        elif action == "listen":
            try:
                internal_sock = self.socket_container.get_by_unix_sock(sock)
            except ValueError:
                self.logger.error("Socket not found in bind table")
                return
            internal_sock.listen = data[0]
            internal_sock.state = States.LISTENING
            out = dict(
                status=0,
                message="Ok",
                data=None
            )
            assert sock == internal_sock.unix_sock
            sock.sendall(VM_Message(out).pack())

        elif action == "accept":
            try:
                internal_sock = self.socket_container.get_by_unix_sock(sock)
                self.accept_queue.put((sock, internal_sock))
            except:
                self.logger.error("Socket not found in bind table")
                return

        elif action == "send":
            pass
        else:
            raise NotImplementedError

    @staticmethod
    def read_packet(sock: socket.socket) -> tuple:
        raw, addr = sock.recvfrom(VM.MSS)
        p = Packet.unpack(raw)
        return p, addr

    @staticmethod
    def read_message(sock: socket.socket) -> VM_Message:
        data = b""
        data += sock.recv(VM_Message.HEADER_SIZE)
        if not data:
            raise EOFError("Socket closed")

        assert len(data) == VM_Message.HEADER_SIZE
        msg = VM_Message.unpack_header(data)
        data += sock.recv(msg.payload_length)
        return VM_Message.unpack(data)

    def __del__(self):
        os.remove("/tmp/RUDP_VM.sock")
        self.udp_sock.close()
        self.unix_sock.close()


class InternalSocket(object):
    def __init__(self, sock: socket.socket, b_context: tuple):
        self.unix_sock = sock  # unix socket
        self.b_context = b_context  # <iface, port>
        self.listen = 0
        self.remote_addr = None  # <ip, port>
        self.state = States.CLOSED
        self.delivered = False

    def __str__(self):
        out = ""
        out += "Bind context:\t{}\n".format(self.b_context)
        out += "Listen:\t{}\n".format(self.listen)
        out += "Remote addr:\t{}\n".format(self.remote_addr)
        out += "State:\t{}\n".format(self.state)
        return out


class InternalSocketContainer(object):
    """
    Inserts new socket only on binding
    """

    def __init__(self):
        self.container = []

    @contract(b_context='tuple[2]')
    def bindable(self, b_context: tuple):
        for sock in self.container:
            if sock.b_context[1] == b_context[1]:
                return False
        return True

    @contract
    def insert(self, sock: InternalSocket):
        if sock in self.container:
            raise RuntimeError("Inserting same socket twice")
        self.container.append(sock)

    @contract
    def count_zombies(self, port: int):
        result = filter(lambda x: x.b_context[1] == port and x.state == States.SYN_RCVD, self.container)
        lst = list(result)
        return len(lst)

    @contract
    def get_by_unix_sock(self, sock: socket.socket):
        result = filter(lambda x: x.unix_sock == sock, self.container)
        lst = list(result)
        if len(lst) == 0:
            raise ValueError("Found {} sockets in container".format(len(lst)))
        return lst[0]

    @contract
    def get_by_port(self, port: int):
        result = filter(lambda x: x.b_context[1] == port, self.container)
        lst = list(result)
        if len(lst) == 0:
            raise ValueError("Found {} sockets in container".format(len(lst)))
        return lst[0]

    @contract
    def get_by_connection(self, local_port: int, remote_addr: tuple):
        result = filter(lambda x: x.b_context[1] == local_port and x.remote_addr == remote_addr,
                        self.container)
        lst = list(result)
        if len(lst) != 1:
            raise ValueError("Found {} sockets in container".format(len(lst)))
        return lst[0]

    @contract
    def get_undelivered(self, local_port: int):
        result = filter(lambda x: x.b_context[1] == local_port and
                                  x.state == States.ESTABLISHED and x.delivered == False, self.container)
        lst = list(result)
        if len(lst) == 0:
            return None
        return lst[0]

    def get_by_filter(self, fil) -> InternalSocket:
        result = filter(fil, self.container)
        lst = list(result)
        if len(lst) != 1:
            raise  ValueError("Found {} sockets".format(len(lst)))
        return lst[0]

    @contract
    def forget(self, sock: InternalSocket):
        self.container.remove(sock)

    def __str__(self):
        out = "____________________________-\n"
        for item in self.container:
            out += item.__str__() + "\n"
        return out


if __name__ == "__main__":
    VM = VM()
    VM.ioloop_start()
