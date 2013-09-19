from apininja.helpers import *
from apininja.log import log
from .container import *

class DatabaseMetaclass(SelfRegisteringType):
    extension = 'Database'
        
class Database(Configurable, metaclass =DatabaseMetaclass ):
    name = ''
    connection = ''
    adapter = ''
    default_limit = 50
    max_limit = 500
    db = None
    system_config = None
    
    def __init__(self, app, adapter, config=None, context= None):
        super().__init__(config)
        self.app = app
        self.data_adapter = adapter
        self.context = context
        self.db = self.connect()
        if not self.system_config:
            self.system_config = {
                'name': self.data_adapter.system_container,
                '_t': 'container',
                'item_type':'container'
                }
        self.system_container = self.get_system_container()

    @property
    def database(self):
        return self
        
    def connect(self):
        return self.data_adapter.connect(self.connection)
        
    def list(self,query={},limit=0,skip=0,select=None,**options):
        if not limit:
            limit = self.default_limit
        return self.system_container.list(query,limit,skip,select,**options)
        
    def get(self,id):
        return self.system_container.get(id)
        
    def create(self,obj):
        return self.system_container.create(obj)
        
    def update(self,obj):
        return self.system_container.update(obj)
        
    def delete(self,obj):
        return self.system_container.delete(obj)
        
    def options(self,obj):
        return [LIST,GET,CREATE]
        
    def get_system_container(self):
        type_name = self.system_config['_t']
        t = find_type(type_name)
        container =  t(self, self.system_config, context = self.context)
        return container
        
    def make_command(self,action, container, query={}, data = None, select=None,**options):
        return Command(self,action,container,self.context,query=query,data=data,select=select,**options)
        
    def close(self):
        self.data_adapter.close_connection(self.db)
        
    def __del__(self):
        self.close()
        

class Command():
    def __init__(self, database, action, container,context, query={}, data = None, select=None,**options):
        self.database = database
        self.action = action
        self.container = container
        self.context = context
        self.query = query
        self.data = data
        self.select = select
        for k,v in options.items():
            setattr(self,k,v)
        self.options = options