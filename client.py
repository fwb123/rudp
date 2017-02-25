from RUDPSocket import RUDPSocket

c = RUDPSocket()
c.connect(('',8080))

# c.send("Hello")