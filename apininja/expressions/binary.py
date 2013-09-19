from . expression import *
import operator

class BinaryExpression (Expression):
    symbol = ''
    operator = None

    def __init__(self,left, right, symbol, operator):
        self.left = left
        self.right = right
        self.symbol = symbol
        self.operator = operator
        
    def execute(self):
        return self.operator(self.left(),self.right())
        
    def __str__(self):
        return '%s %s %s'%(str(self.left),self.symbol,str(self.right))
        
def make_binary(node_type,symbol,op):
    class Binary(BinaryExpression):
        node_type = node_type
        def __init__(self,left,right):
            super().__init__(left,right,type,symbol,operator)
            
    Binary.__name__ = type[0].upper() + type[1:]
    return Binary
        
        
LessThanExpression = make_binary('lessThan','<',operator.lt)
LessThanOrEqualExpression = make_binary('lessThanOrEqual','<=',operator.le)
EqualExpression = make_binary('equal','==',operator.eq)
NotEqualExpression = make_binary('notEqual','!=',operator.ne)
GreaterThanOrEqualExpression = make_binary('greaterThanOrEqual','>=',operator.ge)
GreaterThanExpression = make_binary('greaterThan','>=',operator.gt)

IsExpression = make_binary('is','is',operator.is_)
IsNotExpression = make_binary('isNot','is not',operator.is_not)

AddExpression = make_binary('add','+',operator.add)
AndExpression = make_binary('and','and',operator.and_)
FloordivExpression = make_binary('floordiv','//',operator.floordiv)
LShiftExpression = make_binary('lShift','<<',operator.lshift)
ModExpression = make_binary('mod','%',operator.mod)
MultiplyExpression = make_binary('multiply','*',operator.mul)
OrExpression = make_binary('or','or',operator.or_)
PowerExpression = make_binary('power','**',operator.power)
RShiftExpression = make_binary('rShift','>>',operator.rshift)
SubExpression = make_binary('sub','-',operator.sub)
DivisionExpression = make_binary('division','/',operator.truediv)
XorExpression = make_binary('xor','^',operator.xor)

ConcatExpression = make_binary('concat','+',operator.concat)
ContainsExpression = make_binary('contains','in',operator.contains)
