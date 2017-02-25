import time

from RUDPSocket import RUDPSocket

s = RUDPSocket()
s.bind(('',8080),)
s.listen(10)

c = s.accept()
print(c.remote_addr)
# data = c.recv(5)
# print(data)

time.sleep(100)