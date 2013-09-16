import datetime, time
from bson.objectid import ObjectId, InvalidId
from bson.dbref import DBRef
from copy import *
from helpers import *

simple_types = [
    str,
    int,
    datetime.datetime,
    bool,
    ObjectId,
    DBRef,
    bytes,
    float
    ]
    
def issimple(t):
    return t in simple_types

class DataMeta(type):
    pass

class DataObject(metaclass=DataMeta):
    __metadata__ = None
    default_data = {}
    
    def __init__(self,parent,user,data):
        if parent is None:
            raise ValueError('parent')
        elif user is None:
            raise ValueError('user')
        elif data is None:
            raise ValueError('data')
        self._parent = parent
        self._user = user
        self._data = data
        if '_t' not in data:
            t = type(self)
            if t:
                self._data['_t'] = t.name
        if '_created_by' not in data:
            try:
                try:
                    id = ObjectId(user.id)
                except InvalidId:
                    id = user.id
                db_user = DBRef('users',id)
                self._data['_created_by'] = db_user
            except Exception as ex:
                pass            

    @property
    def id(self):
        try:
            return str(self._data['_id'])
        except KeyError:
            return None

    @property
    def parent(self):
        return self._parent

    @property
    def path(self):
        return self.get_path()

    @property
    def web_path(self):
        return self.get_path(delimiter='/')

    @property
    def type_path(self):
        return self.get_path(delimiter='.')

    @property
    def user(self):
        return self._user

    @property
    def read_roles(self):
        try:
            return self._data['read_roles']
        except KeyError:
            return []

    @property
    def write_roles(self):
        try:
            return self._data['write_roles']
        except KeyError:
            return []

    def get_path(self,delimiter='_'):
        id = self.id
        if id is None:
            id = ''
        if self.parent is self:
            return id
        parent_path = self.parent.get_path(delimiter=delimiter)
        if not parent_path:
            return id
        return parent_path + delimiter + id

    def can_read(self,user):
        if user is ROOT:
            return True
        elif len(self.read_roles) == 0:
            return True
        for r in user.roles:
            if r in self.read_roles:
                return True
            elif r == 'root':
                return True
        return self.can_write(user)

    def can_write(self,user):
        if user is ROOT:
            return True
        for r in user.roles:
            
            if r in self.write_roles:
                return True
            elif r == 'root':
                return True
        return False

    def __getitem__(self,key):
        try:
            return getattr(self,key)
        except AttributeError:
            raise KeyError(key)

    def __setitem__(self,key,value):
        try:
            return setattr(self,key,value)
        except AttributeError:
            raise KeyError(key)

    def __delitem__(self,key):
        try:
            return delattr(self,key)
        except AttributeError:
            raise KeyError(key)

    def __eq__(self,other):
        if isinstance(other,dict):
            return self._data == other
        return super().__eq__(other)

    def __repr__(self):
        return '<%s \'%s\'>'%(type(self).name,self.id)

class DataType(DataObject):
    known_types = {
        'str':str,
        'int':int,
        'float':float,
        'datetime':datetime.datetime,
        'bool':bool,
        'oid':ObjectId,
        'bytes':bytes,
        'ref':DBRef,
        }
    
    def __init__(self,parent,user,data):
        super().__init__(parent,user,data)
        self._inner_type = None
        self._attributes = None
        DataType.known_types[self.name]=self

    @property
    def id(self):
        return self.name

    @property
    def name(self):
        try:
            return self._data['name']
        except:
            return 't%s'%id(self)

    @property
    def base(self):
        try:
            return self._data['base']
        except:
            return 'obj'

    @property
    def parent(self):
        if self._parent is ROOT and self.base != 'obj':
            self._parent= DataType.find_type(self.base)
        return self._parent

    @property
    def attributes(self):
        if not self._attributes:
            try:
                attrs = self._data['attributes']
            except KeyError:
                attrs = {}
                self._data['attributes'] = attrs
            
            try:
                attr_data = self._data['_attributes']
            except KeyError:
                attr_data = {'_id':'attributes'}
                self._data['_attributes'] = attr_data
            self._attributes = AttributeList(self,self.user,attr_data,attrs)
        return self._attributes

    @property
    def inner_type(self):
        if not self._inner_type:
            base = (DataObject,)
            if self.parent is not self:
                base = (self.parent.inner_type,)
            t = DataMeta(self.name,base,{})
            self.apply_to_type(t)
        return self._inner_type
    
    def isinstance(self,other):
        if other.__metadata__ is self:
            return True
        elif self.parent is self:
            return False
        else:
            return self.parent.isinstance(other)

    def issubclass(self,other):
        if other is self:
            return True
        elif self.parent is self:
            return False
        else:
            return self.parent.issubclass(other)

    def apply_to_type(self,cls):
        if not builtins.isinstance_orig(cls,DataMeta):
            raise TypeError('cls')
        elif self._inner_type:
            raise TypeError('%s already exists'%self.name)
        cls.__metadata__ = self
        cls.__name__ = self.name
        self._inner_type = cls
        
        for attr in self.attributes:
            if not hasattr(cls,attr.name):
                attr.apply_to(cls)
        return self
        
    def add_attribute(self,attr):
        if isinstance(attr,dict):
            attr = DataAttribute(self,self.user,attr)
        try:
            attrs = self._data['attributes']
        except KeyError:
            attrs = {}
            self._data['attributes'] = attrs
        attrs[attr.name] = attr
        self.attributes._items.append(attr)
        setattr(self.inner_type,attr.name,attr)

    @staticmethod
    def find_type(meta):
        if meta is None:
            return None
        elif isinstance(meta,str):
            return DataType.known_types[meta]
        elif isinstance(meta,DataType):
            return meta
        elif isinstance(meta,dict):
            if not 'attributes' in meta:
                meta = {'attributes':meta}
            dt = DataType(ObjectType,ROOT,meta)
            return dt
        else:
            raise TypeError(meta)

    def __call__(self,*args,**kwargs):
        return self.inner_type(*args,**kwargs)

    def __getattr__(self,name):
        for attr in self.attributes:
            if attr.name == name:
                return attr
        raise AttributeError(name)
        
    def __getitem__(self,key):
        try:
            return self.attributes[key]
        except AttributeError:
            return super().__getitem__(key)
        
    def __bool__(self):
        return True
       
    def __repr__(self):
        return '<%s \'%s\'>'%(type(self).name,self.id)
       
    def __str__(self):
        return self.name

class DataAttribute(DataObject):

    def __init__(self,parent,user,data):
        super().__init__(parent,user,data)
        self._data_type = None
        
    @property
    def id(self):
        return self.get_path(delimiter='.')
        
    @property
    def name(self):
        try:
            return self._data['name']
        except KeyError:
            return ''

    @property
    def type(self):
        try:
            return self._data['type']
        except KeyError:
            return None

    @property
    def item_type(self):
        try:
            return self._data['item_type']
        except KeyError:
            return None

    @property
    def data_type(self):
        if not self.type:
            return None
        if not self._data_type:
            self._data_type = DataType.find_type(self.type)
            if self.item_type:
                self._data_type = self._data_type.make_derived_type(self.item_type)
        return self._data_type
    
    @property
    def default(self):
        try:
            return self._data['default']
        except KeyError:
            return None
            
    @default.setter
    def default(self,value):
        if self.data_type and not isinstance(value,self.data_type):
            raise TypeError()
        self._data['default'] = value
    
    
    @property
    def declaring_type(self):
        return self.parent.name
        
    @property
    def in_list(self):
        try:
            l = self._data['in_list']
            if l == 'type':
                return DataType.known_types.values()
            return l
        except KeyError:
            return None

    def can_write(self,user):
        return super().can_write(user) and not self.readonly
            
    def get_path(self,delimiter='_'):
        return self.parent.get_path(delimiter) + delimiter + self.name

    def convert(self,obj,value):
        if value=='null' or value is None:
            return None
    
        if isinstance(value,list):
            if self.type == 'list':
                try:
                    attrs = obj._data['_'+self.name]
                except KeyError:
                    attrs = {}
                    obj._data['_'+self.name] = attrs
                return self.data_type(obj,obj.user,attrs,value)
            else:
                TypeError('cannot convert list')
        elif isinstance(value,dict):
            if issubclass(self.data_type,ContainerMeta):
                if self.type == 'list':
                    raise TypeError('cannot convert dict to list type')
                
                try:
                    attrs = obj._data['_'+self.name]
                except KeyError:
                    attrs = {}
                    obj._data['_'+self.name] = attrs
                return self.data_type(obj,obj.user,attrs,value)
            else:
                return self.data_type(obj,obj.user,value)
        elif self.data_type == datetime.datetime:
            if isinstance(value,str):
                
                return time.strptime(value.split('.')[0],'%Y-%m-%dT%H:%M:%S')
            elif isinstance(value,int):
                return datetime.datetime.fromtimestamp(value)
            elif isinstance(value,time.struct_time):
                value = time.mktime(value)
                return datetime.datetime.fromtimestamp(value)
            elif value is None:
                return None
            else:
                raise TypeError('cannot convert date for %s: %s'%(self.name,value))
        else:
            return self.data_type(value)
            
    def apply_to(self,cls):
        setattr(cls,self.name,self)
    
    def __get__(self,obj,objtype):
        if obj is None:
            return self
        if not obj.can_read(obj.user):
            raise PermissionError()
        elif not self.can_read(obj.user):
            raise PermissionError()

        if self.data_type in simple_types:
            try:
                item= obj._data[self.name]
                if not isinstance(item,self.data_type):
                    item = self.convert(obj,item)
                    obj._data[self.name] = item
                return item
            except KeyError:
                return self.default

        try:
            return getattr(obj,'_'+self.name)
        except AttributeError:
            try:
                raw= obj._data[self.name]
            except KeyError:
                raw= self.default
                if raw is None:
                    if issubclass(self.data_type, ListMeta):
                        raw = []
                    else:
                        raw = {}
                obj._data[self.name] = raw
            if issubclass(self.data_type,ContainerMeta):
                try:
                    attrs = obj._data['_'+self.name]
                except KeyError:
                    attrs = {'_id':self.name}
                    obj._data['_'+self.name] = attrs
                data = self.data_type(obj,obj.user,attrs,raw)
            else:
                data = self.data_type(obj,obj.user,raw)
            setattr(obj,'_'+self.name,data)
            return data

    def __set__(self,obj,value):
        if obj is None:
            setattr(self.parent,self.name,value)

        if not obj.can_write(obj.user):
            raise PermissionError(self.name)
        elif not self.can_write(obj.user):
            raise PermissionError(self.name)  
        elif self.required and value is None:
            raise ValueError('value is required')
        elif self.data_type and not isinstance(value,self.data_type):
            value = self.convert(obj,value)
            
        if self.in_list:
            if value not in self.in_list:
                raise ValueError('value not in list')

        if not self.data_type or self.data_type in simple_types:
            obj._data[self.name]=value
        else:
            value._parent = obj
            value._user = obj.user
            setattr(obj,'_'+self.name,value)
            if isinstance(self.data_type,ContainerType):
                obj._data[self.name]=value._inner
                obj._data['_'+self.name]=value._data
            else:
                obj._data[self.name]=value._data

    def __delete__(self,obj):
        if obj is None:
            delattr(self.parent,self.name)

        if not obj.can_write(obj.user):
            raise PermissionError()
        elif not self.can_write(obj.user):
            raise PermissionError()  
        elif self.required and value is None:
            raise ValueError()
        
        del obj._data[self.name]
        try:
            del obj._data['_'+self.name]
        except KeyError:
            pass

        try:
            delattr(obj,'_'+self.name)
        except AttributeError:
            pass
            
    def __bool__(self):
        return True

ROOT = object()

class Root(DataType):
    def __new__(cls,*args):
        if isinstance(ROOT,DataObject):
            return ROOT
        return super().__new__(cls)
        
    @property
    def path(self):
        return ''
    
ROOT = Root(ROOT,ROOT,{'name':'root','attributes':{}})
Root.__metadata__ = ROOT
ROOT._parent = ROOT
ROOT._user = ROOT


import builtins
builtins.isinstance_orig = builtins.isinstance
def patched_isinstance(ins,cls):
    if cls is patched_type:
        cls = builtins.type_orig
    elif builtins.isinstance_orig(cls,DataType):
        if builtins.isinstance_orig(ins,DataObject):
            return cls.isinstance(ins)
        return False
    return builtins.isinstance_orig(ins,cls)
builtins.isinstance = patched_isinstance

builtins.type_orig = builtins.type
def patched_type(ins):
    if builtins.isinstance_orig(ins,DataObject):
        return ins.__metadata__
    return builtins.type_orig(ins)
builtins.type = patched_type

builtins.issubclass_orig = builtins.issubclass
def patched_issubclass(cls,clsinfo):
    if builtins.isinstance_orig(cls,DataType):
        return cls.issubclass(clsinfo)
    elif builtins.isinstance_orig(clsinfo,DataType):
        return False
    return builtins.issubclass_orig(cls,clsinfo)
builtins.issubclass = patched_issubclass

class ContainerType(DataType):

    def __init__(self,parent,user,data):
        self._item_data_type = None
        super().__init__(parent,user,data)
        

    @property
    def name(self):
        name = self._data['name']
        if self.item_type:
            if isinstance(self.item_type,str):
                name+='_'+self.item_type
            else:
                ct = self.item_data_type
                name+='_'+ct.name
        return name

    @property
    def item_type(self):
        try:
            return self._data['item_type']
        except:
            return None

    @property
    def item_data_type(self):
        if not self._item_data_type and self.item_type:
            self._item_data_type = DataType.find_type(self.item_type)
        return self._item_data_type

    def make_derived_type(self,item_type):
        dat_clone = deepcopy(self._data)
        dat_clone['item_type'] = item_type
        cls = self.__class__
        derived_type = cls(self,self.user,dat_clone)
        return derived_type

class DataContainer(DataObject):
    def __init__(self, parent, user, data, inner):
        if type(self) == DataContainer:
            TypeError('DataContainer not intended to be directly created')
        super().__init__(parent,user,data)
        self._inner = inner
        if not self.item_data_type or self.item_data_type in simple_types:
            self._items = inner
        else:
            self._items = None
    
    #@property
    #def id(self):
    #    return self.get_path(delimiter='.')

    @property
    def item_type(self):
        return type(self).item_type

    @property
    def item_data_type(self):
        return type(self).item_data_type

    def append(self,item):
        raise NotImplemented()
        
    def create_item(self,data):
        if data is None:
            return None
        data_type = self.item_data_type
        if '_t' in data:
            data_type = DataType.find_type(data['_t'])
        return data_type(self.parent,self.user,data)

    def _check_items(self):
        if self._items is None:
            self._load_items()

    def _load_items(self):
        raise NotImplemented()
        
    def __getitem__(self,key):
        try:
             return getattr(self,key)
        except (AttributeError, TypeError):
            self._check_items()
            return self._items[key]

    def __setitem__(self,key,value):
        try:
             setattr(self,key)
        except AttributeError:
            self._check_items()
            return self._items[key]

    def __delitem__(self,key):
        try:
            delattr(self,key)
        except AttributeError:
            self._check_items()
            del self._items[key]
            del self._inner[key]

    def __len__(self):
        self._check_items()
        return len(self._items)

    def __iter__(self):
        self._check_items()
        for x in self._items:
            yield x

    def __eq__(self,other):
        return self._inner == other

class DataList(DataContainer):
    def _load_items(self):
        self._items = [self.create_item(d) for d in self._inner]

    def append(self,item):
        self._check_items()
        if not self.can_write(self.user):
            raise PermissionError()
        elif not isinstance(item,self.item_data_type):
            item=self._convert_value(self.parent,self.user,item)
            
        if self.item_data_type in simple_types:
            self._inner.append(item)
        else:
            item._parent = self.parent
            self._items.append(item)
            self._inner.append(item._data)
        return item
            
    def remove(self,item):
        self._check_items()
        if not self.can_write(self.user):
            raise PermissionError()
        if self.item_data_type in simple_types:
            self._inner.remove(item)
        else:
            self._items.remove(item)
            self._inner.remove(item._data)
    
class AttributeList(DataList):
    def __init__(self, parent, user, data, inner):
        DataObject.__init__(self,parent,user,data)
        self._inner = inner
        self._items = None

    def _load_items(self):
        items = [self.create_item(d) for d in self._inner.values()]
        self._local_items = items
        parent = self.parent
        if parent.parent is not parent:
            parent.parent.attributes._check_items()
            items = parent.parent.attributes._items + items
        self._items = items
        
    @property
    def item_type(self):
        return 'attribute'

    @property
    def item_data_type(self):
        try:
            return AttributeMeta
        except NameError:
            return DataAttribute
            
    def __getitem__(self,key):
        self._check_items()
        if isinstance(key,str):
            for i in self._items:
                if i.name == key:
                    return i
            return getattr(self,key)
        elif isinstance(key,int):
            return self._items[key]
        else:
            raise TypeError('key')

    def __setitem__(self,key,value):
        try:
             setattr(self,key)
        except AttributeError:
            self._check_items()
            return self._items[key]

    def __delitem__(self,key):
        try:
            delattr(self,key)
        except AttributeError:
            self._check_items()
            del self._items[key]
            del self._inner[key]
        
    def append(self,item):
        self._check_items()
        if not self.can_write(self.user):
            raise PermissionError()
        elif not isinstance(item,self.item_data_type):
            item=self._convert_value(self.parent,self.user,item)
            
        self._items.append(item)
        self._local_items.append(item)
        self._inner[item.name] = item._data
        return item
            
    def remove(self,item):
        self._check_items()
        if not self.can_write(self.user):
            raise PermissionError()

        self._items.remove(item)
        del self._inner[item.name]
    
class DataDict(DataContainer):
    
    def _load_items(self):
        self._items = {k:self.create_item(v) for k,v in self._inner.items()}

    def keys(self):
        self._check_items()
        return self._items.keys()

    def values(self):
        self._check_items()
        return self._items.values()
    
    def items(self):
        self._check_items()
        return self._items.items()
        
    def append(self,item):
        self._check_items()
        if not self.can_write(self.user):
            raise PermissionError()
        elif not isinstance(item,self.item_data_type):
            item=self._convert_value(self.parent,self.user,item)
            
        try:
            name = item.name
        except AttributeError:
            name = item.id
            
        if self.item_data_type in simple_types:
            self._inner[name] = item
        else:
            item._parent = self.parent
            self._items[name] = item
            self._inner[name]=item._data
        return item

        
ObjectType = DataType(
    ROOT,
    ROOT,
    {
        'name':'obj',
        'attributes':{
            '_id':{
                'name':'_id',
                'type':'oid',
                'readonly':True
            },
            '_t':{
                'name':'_t',
                'type':'str',
                'readonly':True
            },
            'created':{
                'name':'created',
                'type':'datetime',
                'readonly':True
            },
            'created_by':{
                'name':'created_by',
                'type':'ref',
                'readonly':True
            },
            'last_updated':{
                'name':'last_updated',
                'type':'datetime',
                'readonly':True
            }
        }
        }
    )
ObjectType._parent = ObjectType
ObjectType.apply_to_type(DataObject)

TypeMeta = DataType(
    ObjectType,
    ROOT,
    {
        'name':'type',
        'attributes':{
            'name':{
                'name':'name',
                'type':'str',
                },
            'attributes':{
                'name':'attributes',
                'type':'dict',
                'item_type':'attribute'
                }
            }
        }
    )
TypeMeta.apply_to_type(DataType)
TypeMeta.__metadata__ = TypeMeta
ObjectType.__metadata__ = TypeMeta

DataType(
    TypeMeta,
    ROOT,
    {
        'name':'root',
        'attributes':{}
        }
    ).apply_to_type(Root)

AttributeMeta=DataType(
    ObjectType,
    ROOT,
    {
        'name':'attribute',
        'attributes':{
            'name':{
                'name':'name',
                'type':'str',
                },
            'type':{
                'name':'type',
                'type':'str',
                'default':None,
                'in_list':'type',
                'required':True
                },
            'item_type':{
                'name':'item_type',
                'type':'str',
                'default':None,
                'in_list':'type',
                'required':False
                },
            'default':{
                'name':'default',
                'type':None,
                'default':None
                },
            'required':{
                'name':'required',
                'type':'bool',
                'default':False
                },
            'readonly':{
                'name':'readonly',
                'type':'bool',
                'default':False
                },
            'declaring_type':{
                'name':'declaring_type',
                'type':'str',
                'readonly':True
                },
            'in_list':{
                'name':'in_list',
                'type':'list'
                },
            }
        }
    ).apply_to_type(DataAttribute)
        
ContainerMeta = ContainerType(
    ObjectType,
    ROOT,
    {
    'name':'enumerable',
    'attributes':{
        'item_type':{
            'name':'item_type',
            'type':None,
            'default':None
            }
            }
        }
    ).apply_to_type(DataContainer)
            
ListMeta = ContainerType(
    ContainerMeta,
    ROOT,
    {
        'name':'list',
        'attributes':{ }
        }
    ).apply_to_type(DataList)  
    
ContainerType(
    ListMeta,
    ROOT,
    {
        'name':'list',
        'item_type':'attribute',
        'attributes':{}
        }
    ).apply_to_type(AttributeList) 
        
ContainerType(
    ContainerMeta,
    ROOT,
    {
        'name':'dict',
        'attributes':{ }
        }
    ).apply_to_type(DataDict)      
    

def make_object(data,parent=ROOT,user=ROOT):
    type = None
    try:
        type = data['_t']
    except KeyError:
        raise TypeError('type not specified')
    data_type = DataType.find_type(type)
    return data_type(parent,user,data)
