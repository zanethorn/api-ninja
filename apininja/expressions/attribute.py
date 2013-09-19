from . expression import *

class AttributeExpression (Expression):
    def __init__(self,instance,att_name):
        self.instance = instance
        self.name = att_name

class GetAttributeExpression (Expression):
    node_type = 'get_attribute'

    def __init__(self,instance,att_name):
        super().__init__(instance,att_name)
        
    def execute(self):
        ins = self.instance()
        name = self.name()
        return getattr(ins,name)
        
class SetAttributeExpression (Expression):
    node_type = 'set_attribute'

    def __init__(self,instance,att_name, value):
        super().__init__(instance,att_name)
        self.value = value
        
    def execute(self):
        ins = self.instance()
        name = self.name()
        value = self.value()
        return setattr(ins,name,value)