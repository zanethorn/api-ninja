from . expression import *

class ConstantExpression (Expression):
    node_type = 'constant'

    def __init__(self,value):
        self.value = value
        
    def execute(self):
        return self.value