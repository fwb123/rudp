

class ConnectionTable(object):
    def __init__(self):
        self.zombies = []  # list of socket.socket
        self.connected = []  # list of socket.socket
