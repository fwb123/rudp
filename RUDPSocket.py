
class RUDPSocket:
	def __init__(self):
		self.bound = False
		self.port = 0
		self.listen = 0
		self.sock_id = uuid.uuid4()
		instance.add_socket(self)

	def listen(n):
		#precondition
		assert n >= 0
		self.listen = n


	def bind(self, context = None):
		"""
			context: <iface, port>
		"""
		#precondition
		assert self.bound == False 
		assert self.port == 0 
		
		if context:
			#precondition
			assert type(context) == tuple
			assert len(context) == 1
			assert type(context[0]) == int
			
			b_context = BindContext(self.sock_id, context[0])
			if instance.bindable(b_context):
				instance.bind(b_context)
				self.bound = True
				self.port = context[0] 
			else:
				raise Exception("Binding failed")
			return

		port = 0
		while port == 0:
			 	port = random.randrange(0,2**16 - 1)
 				b_context = BindContext(self.sock_id, port)
			 	if instance.bindable(b_context):
					instance.bind(b_context)
			 		self.bound = True
			 		self.port = port

	def read(self, buff_size):
		#precondition
		assert buff_size > 0

		raise NotImplementedError

	def write(self, payload):
		#precondition
		assert len(payload) > 0

		raise NotImplementedError

	def connect(self, addr):
		"""
			addr: <ip, port>
		"""
		#precondition:
		assert type(addr) == tuple
		assert len(addr) == 2
		assert type(addr[0]) == str
		assert type(addr[1]) == int

		addr = VN.Addr(addr[0], addr[1])


	def close(self):
		instance.remove_socket(self)

