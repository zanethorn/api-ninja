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
        self.item_type = None
        self.readonly = False
        self.default = None
        self.required = False
        self.parent_type = None
        self.server_only = False
        
        for k,v in kwargs.items():
            setattr(self,k,v)
        
    @property
    def data_type(self):
        return find_type(self.type,self.item_type)
        
    def __get__(self,obj,objtype):
        if obj is None:
            return self
            
        t = self.data_type
        field_name = self.name

        try:
            item = obj._data[self.name]
        except KeyError:
            item= self.default
            
        if t:
            if not isinstance(item,t):
                if item is None and self.default is None:
                    return None
            
                if issubclass(t,ObjectCollection):
                    try:
                        metadata = obj._data['_'+self.name]
                        
                    except KeyError:
                        metadata = {'field':self.name,'item_type':self.item_type}
                        obj._data['_'+self.name] = metadata
                        
                    if not item:
                        if self.type == 'list':
                            item = []
                        elif self.type == 'dict':
                            item = {}
                        else:
                            raise TypeError('Unknown collection type')
                        obj._data[self.name] = item
                        
                    item = t(obj,metadata,obj.context,item)
                elif issubclass(t,DataObject):
                    if not item:
                        item = {}
                        obj._data[self.name] = item
                    item = t(parent=obj,data=item,context=obj.context)
                elif t is datetime.datetime:
                    item = convert_date(item)
                else:
                    try:
                        item = t(item)
                    except:
                        raise TypeError('Could not cast %s to %s',item,t)
        return item
        
    def __set__(self,obj,value):
        if not obj:
            setattr(self.parent_type, self.name,value)
            del self
        
        if self.readonly:
            raise AttributeError('%s is readonly'%self.name)
            
        if self.required and not value:
            raise ValueError('%s is required'%self.name)
            
        t = self.data_type
        if isinstance(value,ObjectCollection):
            obj._data['_'+self.name] = value._data
            value = value._inner
            
        elif isinstance(value,DataObject):
            value = value._data
            
        elif isinstance(value,list):
            if self.type == 'list':
                if self.item_type:
                    it = find_type(self.item_type)
                    if issubclass(it,DataObject):
                        pass
                    elif it is datetime.datetime:
                        value = [ convert_date(i) for i in value]
                    else:
                        value = [ it(i) for i in value]
            else:
                raise TypeError('No clue what is going on here')
        elif isinstance(value,dict):
            pass
            
        elif t and not isinstance(value,t):
            if t is datetime.datetime:
                item = convert_date(item)
            else:
                try:
                    value = t(item)
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
        if not self.read_roles:
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
        cls.__read_roles__ = lst
        return cls
    return wrapper
    
def write_roles(lst):
    def wrapper(cls):
        cls.__write_roles__ = lst
        return cls
    return wrapper
    
def roles(read,write):
    def wrapper(cls):
        cls.__read_roles__ = read
        cls.__write_roles__ = write
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
        return type.__subclasscheck__(cls,subclass)
        
    def __repr__(self):
        return '<type: %s >' % self.__name__
        
    def add_attribute(cls,attribute):
        cls.__attributes__.append(attribute)
        setattr(cls,attribute.name,attribute)
        
def find_type(name,item_type=None):
    if name is None:
        return None
    if name == 'type':
        name = 'container'
    
    if item_type:
        try:
            return DataObjectType.known_types['%s_%s'%(name,item_type)]
        except KeyError:
            pass
    try:
        if item_type:
            t= make_type('%s_%s'%(name,item_type),{},name)
            t.item_type = item_type
            return t
        else:
            return DataObjectType.known_types[name]
    except KeyError:
        raise TypeError('Type \'%s\' could not be found'%name)
        
def make_type(name,attributes,parent='object', read_roles= None,write_roles = None,**kwargs):
    dct = {}
    bases = (find_type(parent), )
    for attr_name, config in attributes.items():
        attr = DataAttribute(attr_name,**config)
        dct[attr_name] = attr
        
    cls = DataObjectType(name,bases,dct)
    cls.__metadata__ = kwargs
    cls.__name__ = name
    
    return cls
        
@known_type('object')
class DataObject(metaclass = DataObjectType):
    last_updated = attribute('last_updated',type='datetime',default=None, readonly= True)
    created = attribute('created',type='datetime',default=None, readonly=True)
    read_roles = attribute('read_roles',type='list',item_type='str',default=[], server_only = True)
    write_roles = attribute('write_roles',type='list',item_type='str',default=[],server_only = True)
    
    def __init__(self,parent=None,data={}, context=None):
        assert isinstance(data,dict)
        if not context and parent:
            context = parent.context
        
        self._parent = parent
        self._data = data
        self._context = context
        
        assert context
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
        
    def to_simple(self,context=None, can_write=False, server_only = False):
        t = type(self)
        if context is None:
            context = self.context
        attrs = t.__attributes__
        output = { }

        try:
            output['_t'] = self._data['_t']
        except KeyError:
            output['_t'] = type(self).__name__
            
        output['_id'] = self.id
            
        for a in attrs:
            if can_write:
                if a.can_write(context):
                    if server_only or not a.server_only:
                        try:
                            val = getattr(self,a.name)
                            if a.data_type and issubclass(a.data_type,ObjectCollection):
                                output['_'+a.name] = self._data['_'+a.name]
                            if isinstance(val,DataObject):
                                val = val.to_simple(context = context, can_write= can_write,server_only = server_only)
                            if val == a.default:
                                continue
                            output[a.name] = val
                            
                        except KeyError:
                            pass
            else:
                if a.can_read(context):
                    if server_only or not a.server_only:
                        try:
                            val = getattr(self,a.name)
                            if a.data_type and issubclass(a.data_type,ObjectCollection):
                                output['_'+a.name] = self._data['_'+a.name]
                            if isinstance(val,DataObject):
                                val = val.to_simple(context = context, can_write= can_write,server_only = server_only)
                            output[a.name] = val
                        except KeyError:
                            pass
        return output
        
    def can_read(self,context = None):
        if not context:
            context = self.context
        if not context:
            return True
            
        if str(context.user.id) == str(self.id):
            return True
            
        if context.user.id == 'root':
            return True
            
        if not self.read_roles:
            return True
            
        for r1 in user.roles:
            if r1 == 'root':
                return True
            for r2 in self.read_roles:
                if r1 == r2:
                    return True
        return False

class ObjectCollection(DataObject):
    item_type = attribute()
    field = attribute(required=True)
    
    def __init__(self,parent=None, metadata={}, context=None, inner=None ):
        self.item_data_type = None
        super().__init__(parent,metadata,context)
        if self.item_type:
            self.item_data_type = find_type(self.item_type)
        self._inner = inner
        self._items = None
        
    @property
    def id(self):
        return self.field
        
    def ensure_items(self):
        if not self._items:
            self._items = self.load_items()
        
    def load_items(self):
        raise NotImplementedError()
        
    def make_item(self,data):
        if data is None:
            return None
            
        if not self.item_type:
            return data
            
        t= find_type(self.item_type)
        if isinstance(data,dict):
            try:
                t_name = data['_t']
                t = find_type(t_name)
            except KeyError:
                pass
                
        if not isinstance(data,t):
            if issubclass(t,DataObject):
                data = t(parent = self.parent,data = data, context = self.parent.context)
            else:
                data = t(data)

        return data
        
    def to_simple(self,context=None, can_write=False, server_only = False):
        #self.ensure_items()
        return self._inner
        
    def __getitem__(self,key):
        self.ensure_items()
        return self._items[key]
                    
    def __setitem__(self,key,value):
        self.ensure_items()
        self._items[key]
        
    def __delitem__(self,key):
        self.ensure_items()
        del self._items[key]
        del self._inner[key]
        
    def __iter__(self):
        self.ensure_items()
        for x in self._items:
            yield x
            
    def __len__(self):
        self.ensure_items()
        return len(self._items)
        
@known_type('list')
class ObjectList(ObjectCollection):
    def load_items(self):
        return [ self.make_item(d) for d in self._inner ]
        
    def append(self,item):
        self.ensure_items()
        self._items.append(item)
        self._inner.append(item._data)
        
    def remove(self,item):
        self.ensure_items()
        for ix, i in enumerate(self._items):
            if item.id == i.id:
                del self._items[ix]
                break
                
        for ix, i in enumerate(self._inner):
            if item._data == i:
                del self._inner[ix]
                break
        
@known_type('dict')
class ObjectDict(ObjectCollection):
    def load_items(self):
        return { k: self.make_item(v) for k,v in self._inner.items() }
        

    