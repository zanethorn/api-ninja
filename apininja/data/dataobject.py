import datetime
from apininja.log import log
from apininja.helpers import *

simple_types = [
    str,
    int,
    datetime.datetime,
    bool,
    bytes,
    float
    ]

class DataAttribute():

    def __init__(self, name, **kwargs):
        self.name = name
        self.read_roles = []
        self.write_roles = []
        self.type = None
        self.readonly = False
        self.default = None
        self.required = False
        self.data_type = None
        self.parent_type = None
        self.server_only = False
        
        for k,v in kwargs.items():
            setattr(self,k,v)
        if self.type:
            self.data_type = find_type(self.type)
        
    def __get__(self,obj,objtype):
        if obj is None:
            return self
            
        try:
            return obj._data[self.name]
        except KeyError:
            return self.default
        
    def __set__(self,obj,value):
        if not obj:
            setattr(self.parent_type, self.name,value)
            del self
        
        if self.readonly:
            raise AttributeError('%s is readonly'%self.name)
            
        if self.required and not value:
            raise ValueError('%s is required'%self.name)
            
        if self.data_type and not isinstance(value,self.data_type):
            try:
                value = self.data_type(value)
            except:
                raise TypeError('%s expected value of type %s',(self.name,self.type))
            
        obj._data[self.name] = value
        
    def __repr__(self):
        return '<attribute: %s:%s >' %(self.name,self.type)
        
    def can_read(self,context):
        user = context.user
        if user.id == 'root':
            return True
        if not self.read_roles:
            return True
        for r1 in user.roles:
            if r1 == 'root':
                return True
            for r2 in self.read_roles:
                if r1 == r2:
                    return True
        return self.can_write(context)
        
    def can_write(self,context):
        if self.readonly:
            return False
        user = context.user
        if user.id == 'root':
            return True
        for r1 in user.roles:
            if r1 == 'root':
                return True
            for r2 in self.write_roles:
                if r1 == r2:
                    return True
        return False
        
def attribute(name='', **kwargs):
    return DataAttribute(name,**kwargs)
    
# class TypeMetadata():
    # def __init__(self,base):
        # self.name = ''
        # self.attributes = []
        # self.base = base
        # self.read_roles = []
        # self.write_roles = []
    
    
def known_type(name):
    def wrapper(cls):
        old_name = cls.__name__
        try:
            del DataObjectType.known_types[old_name]
        except KeyError:
            pass
        cls.__name__ = name
        DataObjectType.known_types[name] = cls
        return cls
    return wrapper
    
def read_roles(lst):
    def wrapper(cls):
        cls.__metadata__['_read_roles'] = lst
        return cls
    return wrapper
    
def write_roles(lst):
    def wrapper(cls):
        cls.__metadata__['_write_roles'] = lst
        return cls
    return wrapper
    
def roles(read,write):
    def wrapper(cls):
        cls.__metadata__['_read_roles'] = read
        cls.__metadata__['_write_roles'] = write
        return cls
    return wrapper

class DataObjectType(type):
    known_types= { t.__name__ : t for t in simple_types }
    #__metadata__ = {}
    
    def __new__(meta,name,bases,dct):
        for k,v in dct.items():
            if isinstance(v,DataAttribute):
                if not v.name:
                    v.name = k
        try:
            return meta.known_types[name]
        except KeyError:
            pass
        
        cls = type.__new__(meta,name,bases,dct)
        #cls.__metadata__ = TypeMetadata(bases)
        
        attributes = list(filter(lambda v:isinstance(v,DataAttribute), dct.values()))
        for attr in attributes:
            attr.parent_type = cls
            
        base_attrs = []
        for b in bases:
            try:
                base_attrs += b.__attributes__
            except:
                pass
            
        cls.__attributes__ = base_attrs + attributes
        name = convert_camel_case(name)
        cls.__name__ = name
        log.info('Found DataObject Type %s',name)
        meta.known_types[name] = cls
        return cls
        
    def __init__(cls,name,bases,dct):
        pass

    def __instancecheck__(cls,instance):
        return type.__instancecheck__(cls,instance)

    def __subclasscheck__(cls,subclass):
        return type.__instancecheck__(cls,instance)
        
    def __repr__(self):
        return '<type: %s >' % self.__name__
        
    def add_attribute(cls,attribute):
        cls.__attributes__.append(attribute)
        setattr(cls,attribute.name,attribute)
        
def find_type(name):
    if name == 'type':
        name = 'container'
    try:
        return DataObjectType.known_types[name]
    except KeyError:
        pass
    raise TypeError('Type \'%s\' could not be found'%name)
        
@known_type('object')
class DataObject(metaclass = DataObjectType):
    last_updated = attribute('last_updated',default=None, readonly= True)
    created = attribute('created',default=None, readonly=True)
    
    def __init__(self,parent=None,data={}, context=None):
        self._parent = parent
        self._data = data
        self._context = context
        if not '_t' in data:
            self._data['_t'] = type(self).__name__
        
    def __repr__(self):
        return '<%s: %s >' % (type(self).__name__,self.id)
        
    @property
    def id(self):
        try:
            return self._data['_id']
        except KeyError:
            return None
        
    @property
    def context(self):
        return self._context
        
    @property
    def parent(self):
        return self._parent
        
    def to_dict(self):
        t = type(self)
        attrs = t.__attributes__
        output = { }
        try:
            output['_t'] = self._data['_t']
        except KeyError:
            output['_t'] = type(self).__name__
            
        try:
            output['_id'] = self._data['_id']
        except KeyError:
            output['_id'] = self.id
        
        for a in attrs:
            if a.can_read(self.context) and not a.server_only:
                output[a.name] = getattr(self,a.name)
        
        return output
    
    def to_write_dict(self):
        t = type(self)
        attrs = t.__attributes__
        output = { '_t': self._data['_t'] }
        try:
            output['_id'] = self._data['_id']
        except KeyError:
            pass
        for a in attrs:
            if a.can_write(self.context):
                output[a.name] = getattr(self,a.name)
        
        return output

def make_type(name,attributes,parent='object', read_roles= None,write_roles = None,**kwargs):
    dct = {}
    bases = (find_type(parent), )
    for attr_name, config in attributes.items():
        attr = DataAttribute(attr_name,**config)
        dct[attr_name] = attr
        
    cls = DataObjectType(name,bases,dct)
    cls.__metadata__ = kwargs
    cls.__metadata__['name'] = name
    
    return cls
    