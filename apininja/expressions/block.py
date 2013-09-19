from . expression import *

class BlockExpression (Expression):
    node_type = 'block'

    def __init__(self,*expressions):
        self.expressions = expressions
        
    def execute(self):
        for e in self.expressions:
            r = e()