import random
import socket

from contracts import contract

from VM_Message import VM_Message
from VM import VM

class RUDPSocket:
    def __init__(self):
        self.iface = None
        self.port = 0
        self.listen = 0
        self.bound = False

        self.interface = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.interface.connect("/tmp/RUDP_VM.sock")


    @contract(n='int,>0,<65536')
    def listen(self, n : int):
        self.listen = n


    @contract
    def active_bind(self, iface : str, port : int):
        b_context = (iface, port)
        payload = dict(
            action="is_bindable",
            data=b_context
        )
        msg = VM_Message(payload)
        self.interface.send(msg.pack())
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
                raise Exception(resp["message"])
        else:
            raise ValueError("Not bindable")


    @contract
    def bind(self, context : tuple):
        """
            context: <iface, port>
        """
        # precondition
        assert self.bound == False
        assert self.port == 0
        assert len(context) <= 2

        #Active bind
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

    def read(self, buff_size):
        # precondition
        assert buff_size > 0

        raise NotImplementedError

    def write(self, payload):
        # precondition
        assert len(payload) > 0

        raise NotImplementedError

    def connect(self, addr):
        """
            addr: <ip, port>
        """
        # precondition:
        pass


    def close(self):
        pass