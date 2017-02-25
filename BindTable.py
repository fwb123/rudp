import socket

from contracts import contract


class BindTable:
    def __init__(self):
        self.table = {}  # {sock : <iface, port>}
        self.meta = {}  # { sock: <seq, ack> }
        self.listen = {} # { sock: value }

    @contract(context='tuple[2]')
    def bindable(self, context: tuple):
        for item in self.table.values():
            if item[1] == context[1]:
                return False
        return True

    @contract(context='tuple[2]')
    def insert(self, sock: socket.socket, context: tuple):
        if sock in self.table.keys():
            raise RuntimeError("Inserting same socket twice")
        if self.bindable(context):
            self.table[sock] = context
            self.meta[sock] = 0,0
            self.listen[sock] = 0
        else:
            raise ValueError("Check first")

    @contract
    def get(self, sock: socket.socket) -> tuple:
        return self.table[sock]

    @contract
    def find(self, port: int) -> socket.socket:
        for key, value in self.table.items():
            if value[1] == port:
                return key
        raise ValueError("No socket found")
