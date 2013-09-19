from . expression import *

class LambdaExpression (Expression):
    node_type = 'lambda'
    def __init__(self,body,*args):
        self.body = body
        self.arguments = args
        
    def execute(self):
        for e in self.expressions:
            r = e()