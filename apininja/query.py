from expressions import *
from .helpers import *
import inspect

class Query():
    def __init__(self,expression,provider):
        self._expression = expression
        self._provider = provider

    @property 
    def expression(self):
        return self._expression
        
    @property
    def provider(self):
        return self._provider
        
    def execute(self):
        return self.provider.execute(self)
        
    def __init__(self):
        for i in self.execute():
            yield i
        
    def aggrigate(self,func=None,selector = None,seed=None):
        raise NotImplementedError()
    
    def all(self,func=None):
        raise NotImplementedError()
        
    def any(self,func=None):
        raise NotImplementedError()
        
    def average(self,selector=None):
        raise NotImplementedError()
        
    def concat(self,other):
        raise NotImplementedError()
        
    def contains(self,item,func=None):
        raise NotImplementedError()
        
    def count(self,func=None):
        raise NotImplementedError()
        
    def default(self,value = None):
        raise NotImplementedError()
        
    def distinct(self,func=None):
        raise NotImplementedError()
        
    def element_at(self,index):
        raise NotImplementedError()
        
    def element_at_or_default(self,index):
        raise NotImplementedError()
        
    def exclude(self,other,comparer=None):
        raise NotImplementedError()
        
    def first(self,func=None):
        raise NotImplementedError()
        
    def first_or_default(self,func=None):
        raise NotImplementedError()
        
    def group_by(self,key_func=None,element_func=None,comparer=None):
        raise NotImplementedError()
        
    def group_join(self,inner,outer_key=None,inner_key=None, result_func=None,comparer=None):
        raise NotImplementedError()
        
    def intersect(self,other,comparer=None):
        raise NotImplementedError()
        
    def join(self,inner,outer_key=None,inner_key=None,comparer=None):
        raise NotImplementedError()
        
    def last(self,func=None):
        raise NotImplementedError()
        
    def last_or_default(self,func=None):
        raise NotImplementedError()
        
    def max(self,func=None):
        raise NotImplementedError()
        
    def min(self,func=None):
        raise NotImplementedError()
        
    def order_by(self,selector,comparer=None):
        raise NotImplementedError()
        
    def order_by_descending(self,selector,comparer=None):
        raise NotImplementedError()
        
    def reverse(self):
        raise NotImplementedError()
        
    def select(self,selector):
        raise NotImplementedError()
        
    def select_many(self,selector):
        raise NotImplementedError()

    def single(self,func=None):
        raise NotImplementedError()
        
    def single_or_default(self,func=None):
        raise NotImplementedError()
        
    def skip(self,count):
        raise NotImplementedError()
        
    def skip_while(self,func):
        raise NotImplementedError()
        
    def sum(self,selector=None):
        raise NotImplementedError()
        
    def take(self,count):
        raise NotImplementedError()
        
    def take_while(self,func):
        raise NotImplementedError()
        
    def then_by(self,selector,comparer=None):
        raise NotImplementedError()
        
    def then_by_descending(self,selector,comparer=None):
        raise NotImplementedError()
        
    def union(self,other,comparer=None):
        raise NotImplementedError()
        
    def where(self,func):
        raise NotImplementedError()
        
    def zip(self,other,selector):
        raise NotImplementedError()

class ExpressionVisitor():
    def __init__(self,provider):
        self.provider = provider
        
    def visit(self,exp):
        node_type = exp.node_type
        if node_type == 'get_attribute':
            return self.visit_get(exp)
        elif node_type == 'set_attribute':
            return self.visit_set(exp)
        elif node_type == 'block':
            return self.visit_block(exp)
        elif node_type == 'constant':
            return self.visit_contstant(exp)
        elif node_type == 'conditional':
            return self.visit_conditional(exp)
        elif node_type == 'index':
            return self.visit_index(exp)
        elif node_type in [
            'lessThan',
            'lessThanOrEqual',
            'equal',
            'notEqual',
            'greaterThanOrEqual',
            'greaterThan',
            'is',
            'isNot',
            'and',
            'add',
            'floordiv',
            'lShift',
            'mod',
            'multiply',
            'or',
            'power',
            'rShift',
            'sub',
            'division',
            'xor',
            'concat',
            'contains'
            ]:
            return self.visit_binary(exp)
        else:
            raise ValueError('Unknown node type')
        
    def visit_binary(self,exp):
        left = self.visit(exp.left)
        right = self.visit(exp.right)
        t = type(exp)
        new = t(left,right)
        return new
        
    def visit_get(self,exp):
        ins = self.visit(exp.instance)
        name = exp.name
        t = type(exp)
        new = t(ins,name)
        return new
        
    def visit_set(self,exp):
        ins = self.visit(exp.instance)
        val = self.visit(exp.value)
        name = exp.name
        t = type(exp)
        new = t(ins,name,val)
        return new
        
    def visit_block(self,exp):
        expressions = [ self.visit(e) for e in exp.expressions ]
        t = type(exp)
        new = t(*expressions)
        return new
        
    def visit_conditional(self,exp):
        test = self.visit(exp.test)
        if_true = self.visit(exp.if_true)
        if_false = None
        if exp.if_false:
            if_false = self.visit(exp.if_false)
        t = type(exp)
        new = t(test,if_true,if_false)
        return new
        
    def visit_constant(self,exp):
        value = exp.value
        t = type(exp)
        new =  t(value)
        return new
        
    def visit_index(self,exp):
        ins = self.visit(exp.instance)
        arg = self.visit(exp.arg)
        t = type(exp)
        new = t(ins,arg)
        return new
        
    
        
class QueryProvider():
    visitor = ExpressionVisitor
    
    def execute(self,query):
        v = self.visitor(self)
        exp = query.expression
        visited = v.visit(exp)
        return visited()

    @classmethod
    def aggrigate(iter,func=None,selector = None,seed=None):
        raise NotImplementedError()
    
    @classmethod
    def all(iter,func=None):
        if func is None:
            func = bool
        for i in iter:
            if not func(i):
                return False
        return True
        
    @classmethod
    def any(iter,func=None):
        if func is None:
            func = bool
        for i in iter:
            if func(i):
                return True
        return False
    
    @classmethod
    def average(iter,selector=None):
        raise NotImplementedError()
    
    @classmethod
    def concat(iter,other):
        raise NotImplementedError()
    
    @classmethod
    def contains(iter,item,func=None):
        raise NotImplementedError()
    
    @classmethod
    def count(iter,func=None):
        raise NotImplementedError()
        
    @classmethod
    def default(iter,value = None):
        raise NotImplementedError()
        
    @classmethod
    def distinct(iter,func=None):
        raise NotImplementedError()
    
    @classmethod
    def element_at(iter,index):
        raise NotImplementedError()
    
    @classmethod
    def element_at_or_default(iter,index):
        raise NotImplementedError()
    
    @classmethod
    def exclude(iter,other,selector=None):
        raise NotImplementedError()
    
    @classmethod
    def first(iter,func=None):
        raise NotImplementedError()
    
    @classmethod
    def first_or_default(iter,func=None):
        raise NotImplementedError()
    
    @classmethod
    def group_by(iter,key_func=None,element_func=None,comparer=None):
        raise NotImplementedError()
    
    @classmethod
    def group_join(iter,inner,outer_key=None,inner_key=None, result_func=None,comparer=None):
        raise NotImplementedError()
    
    @classmethod
    def intersect(iter,other,comparer=None):
        raise NotImplementedError()
    
    @classmethod
    def join(iter,inner,outer_key=None,inner_key=None,comparer=None):
        raise NotImplementedError()
    
    @classmethod
    def last(iter,func=None):
        raise NotImplementedError()
    
    @classmethod
    def last_or_default(iter,func=None):
        raise NotImplementedError()
    
    @classmethod
    def max(iter,func=None):
        raise NotImplementedError()
    
    @classmethod
    def min(iter,func=None):
        raise NotImplementedError()
    
    @classmethod
    def order_by(iter,selector,comparer=None):
        raise NotImplementedError()
    
    @classmethod
    def order_by_descending(iter,selector,comparer=None):
        raise NotImplementedError()
    
    @classmethod
    def reverse(iter):
        raise NotImplementedError()
    
    @classmethod
    def select(iter,selector):
        for i in iter:
            yield selector(i)
    
    @classmethod
    def select_many(iter,selector):
        raise NotImplementedError()

    @classmethod
    def single(iter,func=None):
        raise NotImplementedError()
        
    @classmethod
    def single_or_default(iter,func=None):
        raise NotImplementedError()
    
    @classmethod
    def skip(iter,count):
        raise NotImplementedError()
    
    @classmethod
    def skip_while(iter,func):
        raise NotImplementedError()
    
    @classmethod
    def sum(iter,selector=None):
        raise NotImplementedError()
    
    @classmethod
    def take(iter,count):
        raise NotImplementedError()
    
    @classmethod
    def take_while(iter,func):
        raise NotImplementedError()
    
    @classmethod
    def then_by(iter,selector,comparer=None):
        raise NotImplementedError()
    
    @classmethod
    def then_by_descending(iter,selector,comparer=None):
        raise NotImplementedError()
    
    @classmethod
    def union(iter,other,comparer=None):
        raise NotImplementedError()
        
    @classmethod
    def where(iter,func):
        raise NotImplementedError()
        
    @classmethod
    def zip(iter,other,selector):
        raise NotImplementedError()
        

    