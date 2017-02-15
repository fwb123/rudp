
class BindTable:
	def __init__(self):
		self.table = [] #list of BindContext
		
	def bindable(self, context):
		#precondition
		assert isinstance(context, BindContext)

		for item in self.table:
			if BindContext.intersects(item, context):
				return False
		return True

	def insert(self, context):
		assert isinstance(context, BindContext)

		if self.bindable(context):
			self.table.append(context)	
		else:
			raise Exception("Check first")
