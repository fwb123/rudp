
class Addr:
	def __init__(self, ip, port):
		#precondition
		assert type(ip) == str
		assert type(port) == int
		assert port > 0

		self.ip = ip
		self.port = port

	def __to_tuple(self):
		return (self.ip, self.port,)

	def __str__(self):
		out = "IP:\t{}\nPort:\t{}\n".format(self.ip, self.port)
