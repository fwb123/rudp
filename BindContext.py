import uuid

class BindContext:
    def __init__(self, sock_id, port):
        # precondition
        assert type(sock_id) == uuid.UUID
        assert type(port) == int
        assert port > 0

        self.sock_id = sock_id
        self.port = port

    @staticmethod
    def intersects(lhs, rhs):
        # precondition
        assert isinstance(rhs, BindContext)
        assert isinstance(lhs, BindContext)

        if lhs.port == rhs.port:
            return True
        return False
