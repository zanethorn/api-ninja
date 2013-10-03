from .dataobject import *
from apininja.actions import *
from apininja.helpers import *
from datetime import datetime

@known_type('container')
class DataContainer(DataObject):
    item_type= 'object'
    #item_data_type = DataObject
    name = attribute('name',type='str',readonly=True)
    
    def __getattr__(self,name):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(name)
        
    def __setattr__(self,name,value):
        if name[0] == '_':
            super().__setattr__(name,value)
        else:
            self._data[name] = value
    @property    
    def id(self):
        return self.name
            
    @property
    def request(self):
        return self.context.request
        
    @property
    def response(self):
        return self.context.response

    @property
    def database(self):
        return self.parent.database
        
    @property
    def data_adapter(self):
        return self.database.data_adapter
        
    def _handle_config_value(self,name,value):
        if name == 'item_type':
            try:
                value = DataObjectType.known_types[value]
            except KeyError:
                pass
        setattr(self,name,value)
        
    @property
    def name(self):
        return self._data['name']

    def make_item(self,data):
        t= find_type(self.item_type)
        try:
            t_name = data['_t']
            t = find_type(t_name)
        except KeyError:
            pass
        log.debug('%s is making item of type %s',self.name,t)
        return t(parent=self,data=data,context = self.context)

    def connect(self):
        return self.data_adapter.connect(self.connection)

    def list(self,query={},limit=None,skip=0,select=None,**options):
        cmd = self.database.make_command(LIST,self,query=query,limit=limit,skip=skip,select=select, **options)
        result = self.data_adapter.execute_command(cmd)
        return result
        
    def get(self,id):
        query = self.get_id_query(id)
        log.debug('%s using query %s',self.name,query)
        cmd = self.database.make_command(GET,self,query= query)
        result = self.data_adapter.execute_command(cmd)
        if not result:
            return None
        if isinstance(result,dict):
            result = self.make_item(result)
        if not result.can_read(self.context):
            self.response.permission_error()
            
        return result
        
    def create(self,obj):
        if isinstance(obj,dict):
            data = obj
        elif isinstance(obj,DataObject):
            data = obj.to_write_dict()
        else:
            raise TypeError('Expected DataObject, got %s',type(obj).__name__)
        
        now = datetime.utcnow()
        data['last_updated'] = now
        data['created']=now
        
        cmd = self.database.make_command(CREATE,self,data=data)
        result = self.data_adapter.execute_command(cmd)
        
        if not result:
            result = data
        if isinstance(result,dict):
            result = self.make_item(result)
            
        return result
        
    def update(self,obj):
        if isinstance(obj,dict):
            data = obj
        elif isinstance(obj,DataObject):
            data = obj.to_write_dict()
        else:
            raise TypeError('Expected DataObject, got %s',type(obj).__name__)
            
        now = datetime.utcnow()
        data['last_updated'] = now
            
        query = self.get_id_query(data['_id'])
        cmd = self.database.make_command(UPDATE,self,data=data, query=query)
        result = self.data_adapter.execute_command(cmd)
        
        if not result:
            result = data
        if isinstance(obj,DataObject):
            obj._data = result
            result = obj
        elif isinstance(result,dict):
            result = self.make_item(result)
        else:
            raise TypeError('Could not interpret result')
        return result
        
    def delete(self,obj):
        if isinstance(obj,dict):
            data = obj
        elif isinstance(obj,DataObject):
            data = obj._data
        else:
            raise TypeError('Expected DataObject, got %s',type(obj).__name__)
            
        query = self.get_id_query(data['_id'])
        cmd = self.database.make_command(DELETE,self,query=query)
        result = self.data_adapter.execute_command(cmd)
        
        if not result:
            result = data
        if isinstance(result,dict):
            result = self.make_item(result)
            
        return result
        
    def options(self,obj):
        return [GET,UPDATE,DELETE]
       
    def get_id_query(self,id):
        if isinstance(id,dict):
            return id
        pid = self.data_adapter.parse_key(id)
        return {'_id':pid}
        
@known_type('system_container')
class SystemDataContainer(DataContainer):
    item_type= attribute('item_type',default='container')
    item_data_type = DataObject
    
    def make_item(self,data):
        t= self.item_data_type
        log.debug('getting container from %s',data)
        try:
            t_name = data['_t']
            t = find_type(t_name)
        except KeyError:
            try:
                t_name = data['name']
                t = find_type(t_name)
            except KeyError:
                pass
        
        return t(parent=self,data=data,context = self.context)
    
    def get_id_query(self,id):
        return {'name':id}
    