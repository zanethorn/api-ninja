from . expression import *

class IndexExpression (Expression):
    node_type = 'index'

    def __init__(self,instance,arg):
        self.instance = instance
        self.arg = arg
        
    def execute(self):
        ix = self.arg()
        ins = self.instance()
        return ins[ix]