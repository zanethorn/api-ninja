from . expression import *

class ConditionalExpression (Expression):
    node_type = 'conditional'

    def __init__(self,test,if_true,if_false=None):
        self.test = test
        self.if_true = if_true
        self.if_false = if_false
        
    def execute(self):
        if self.test():
            return self.if_true()
        elif self.if_false:
            return self.if_false()