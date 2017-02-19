from contracts import contract


class BindTable:
    def __init__(self):
        self.table = []  # list of BindContext

    @contract(context='tuple[2]')
    def bindable(self, context: tuple):
        for item in self.table:
            if item[1] == context[1]:
                return False
        return True

    @contract(context='tuple[2]')
    def insert(self, context : tuple):
        if self.bindable(context):
            self.table.append(context)
        else:
            raise Exception("Check first")
