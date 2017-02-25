import copy
import random
import socket
import logging

from contracts import contract

from VM_Message import VM_Message
from VM import VM


class RUDPSocket:
    def __init__(self):
        self.iface = None
        self.port = 0
        self.n_listen = 0
        self.bound = False
        self.connected = False
        self.remote_addr = None  # <ip, port>

        self.interface = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.interface.connect("/tmp/RUDP_VM.sock")

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

    @contract(port='int,>0')
    def active_bind(self, iface: str, port: int):
        b_context = (iface, port)
        payload = dict(
            action="is_bindable",
            data=b_context
        )
        msg = VM_Message(payload)
        self.interface.sendall(msg.pack())
        resp = VM.read_message(self.interface).payload
        if resp["status"] == 0:
            payload = dict(
                action="bind",
                data=b_context
            )
            msg = VM_Message(payload)
            self.interface.send(msg.pack())
            resp = VM.read_message(self.interface).payload
            if resp["status"] != 0:
                self.logger.error("Socket is bindable but bind failed")
                raise Exception(resp["message"])
        else:
            self.logger.debug("Socket is not bindable")
            raise ValueError("Not bindable")
        self.logger.debug("Socket bound on {}:{}".format(iface, port))

    @contract
    def bind(self, context: tuple):
        """
            context: <iface, port>
        """
        # precondition
        assert self.bound == False
        assert self.port == 0
        assert len(context) <= 2

        # Active bind
        if len(context) == 2:
            iface, port = context
            self.active_bind(iface, port)
            self.port = port
        else:
            iface, = context
            done = False
            while not done:
                port = random.randrange(0, 2 ** 16 - 1)
                try:
                    self.active_bind(iface, port)
                    done = True
                    self.port = port
                except ValueError:
                    done = False
                    self.port = 0

        self.bound = True

    @contract(n='int,>0,<65536')
    def listen(self, n: int):
        # precondition
        assert self.bound == True
        assert self.port > 0

        self.n_listen = n
        payload = dict(
            action="listen",
            data=(n,)
        )

        msg = VM_Message(payload)
        self.interface.sendall(msg.pack())
        resp = VM.read_message(self.interface).payload
        if resp["status"] != 0:
            self.logger.error("Unknown error on listen")
            raise RuntimeError("Unknown error on listen")

    @contract
    def recv(self, buff_size: int) -> str:
        # precondition
        assert buff_size > 0

        if not self.connected:
            raise ConnectionError("Socket not connected")

        payload = dict(
            action="recv",
            data=(buff_size,)
        )
        self.interface.sendall(VM_Message(payload).pack())
        resp = VM.read_message(self.interface).payload
        if resp["status"] != 0:
            raise RuntimeError(resp["message"])
        else:
            data, = resp["data"]

        return data

    @contract
    def send(self, payload: str) -> None:
        """
        Works as sendall
        """

        # precondition
        assert len(payload) > 0

        if not self.connected:
            raise ConnectionError("Socket not connected")

        payload = dict(
            action="send",
            data=(payload,)
        )
        self.interface.sendall(VM_Message(payload).pack())
        resp = VM.read_message(self.interface).payload
        if resp["status"] != 0:
            raise RuntimeError(resp["message"])

    @contract(addr='tuple[2]')
    def connect(self, addr: tuple):
        """
            addr: <ip, port>
        """
        # precondition
        if not self.bound:
            self.bind(('',))

        self.connected = False

        payload = dict(
            action="connect",
            data=addr
        )
        self.interface.sendall(VM_Message(payload).pack())

        resp = VM.read_message(self.interface).payload
        if resp["status"] == 0:
            self.logger.debug("Connection established with {}:{}".format(*addr))
            self.connected = True
            self.remote_addr = addr
        else:
            self.logger.error("Connection failed")
            raise RuntimeError("Connection failed with status code {}, {}".
                               format(resp["status"], resp["message"]))

    def accept(self) -> 'RUDPSocket':
        if not self.bound or self.listen == 0:
            raise RuntimeError("Socket is not bound or not listening")
        payload = dict(
            action="accept",
            data=()
        )
        self.interface.sendall(VM_Message(payload).pack())
        resp = VM.read_message(self.interface).payload
        if resp["status"] == 0:
            self.logger.debug("New socket spawned")
            sock = copy.copy(self)
            sock.remote_addr = tuple(resp["data"])
            return sock
        else:
            raise RuntimeError("Unknown error on accept")

    def close(self):
        pass


if __name__ == "__main__":
    s = RUDPSocket()
    s.bind(('0.0.0.0',))
    s.connect(('127.0.0.1', 8080))
