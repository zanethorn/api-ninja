import datetime
from apininja.log import log

simple_types = [
    str,
    int,
    datetime.datetime,
    bool,
    bytes,
    float
    ]

class DataAttribute():
    type = None
    name = None
    readonly = False
    default = None
    required = False
    data_type = None

    def __init__(self, name, **kwargs):
        self.name = name
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
        obj._data[self.name] = value
        
def attribute(name, **kwargs):
    return DataAttribute(name,**kwargs)
    
    
def known_type(name):
    def wrapper(cls):
        old_name = cls.__name__
        try:
            del DataObjectType.known_types[old_name]
        except KeyError:
            pass
        cls.__metadata__['_t'] = name
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
    known_types= {}#{ t.__name__ : t for t in simple_types }
    __metadata__ = {}
    
    def __new__(meta,name,bases,dct):
        try:
            return meta.known_types[name]
        except KeyError:
            pass
        
        cls = type.__new__(meta,name,bases,dct)
        attributes = list(filter(lambda v:isinstance(v,DataAttribute), dct.values()))
        cls.__metadata__['attributes'] = attributes
        log.info('Found DataObject Type %s',name)
        meta.known_types[name] = cls
        return cls
        
    def __init__(cls,name,bases,dct):
        pass

    def __instancecheck__(cls,instance):
        print(cls,instance)
        return type.__instancecheck__(cls,instance)

    def __subclasscheck__(cls,subclass):
        print(cls,subclass)
        return type.__instancecheck__(cls,instance)
        
    def add_attribute(cls,attribute):
        cls.attributes.append(attribute)
        setattr(cls,attribute.name,attribute)
        
    @property
    def attributes(cls):
        return cls.__metadata__['attributes']
        
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
   
    def __init__(self,parent=None,data={}, context=None):
        self._parent = parent
        self._data = data
        self._context = context
        if not '_t' in data:
            self._data['_t'] = type(self).__metadata__['_t']
        
    @property
    def context(self):
        return self._context
        
    @property
    def parent(self):
        return self._parent

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
    