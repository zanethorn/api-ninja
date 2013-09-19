
expressions = {}
class ExpressionMetaclass(type):
    def __new__(meta,name,bases,dict):
        cls = type.__new__(meta,name,bases,dict)
        if cls.node_type:
            expressions[node_type] = cls
        return cls

class Expression(metaclass = ExpressionMetaclass):
    node_type = ''
       
    def execute(self):
        raise NotImplementedError()

    def __repr__(self):
        return '<%s: %s>'%(self.node_type,str(self))
        
    def __str__(self):
        raise NotImplementedError()
        
    def __call__(self):
        return self.execute()
        