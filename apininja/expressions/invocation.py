from . expression import *

class InvocationExpression (Expression):
    def __init__(self,func,*expressions):
        super().__init__('invocation')
        self.func = func
        self.expressions = expressions
        
    def execute(self):
        for e in self.expressions:
            r = e()