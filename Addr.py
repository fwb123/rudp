from contracts import contract


class Addr:
    @contract(ip='str', port='int,>0')
    def __init__(self, ip : str, port : int):
        self.ip = ip
        self.port = port

    def __to_tuple(self):
        return (self.ip, self.port,)

    def __str__(self):
        out = "IP:\t{}\nPort:\t{}\n".format(self.ip, self.port)


if __name__ == "__main__":
    a = Addr('11', '4')