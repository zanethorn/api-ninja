from . expression import *

class LoopExpression (Expression):
    def __init__(self,*expressions):
        super().__init__('block')
        self.expressions = expressions
        
    def execute(self):
        for e in self.expressions:
            r = e()