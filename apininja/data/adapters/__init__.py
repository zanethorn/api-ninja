import importlib, os
from apininja.log import log
from apininja.helpers import *
log.info('Initializing apininja.data.adapters namespace')

class AdapterMetaclass(SelfRegisteringType):
    extension = 'Adapter'

class DataAdapter(Configurable, metaclass=AdapterMetaclass):

    def __init__(self,config=None):
        super().__init__(config)
        self.key_type = int
    
    def parse_key(self, s):
        try:
            return self.key_type(s)
        except:
            log.debug('%s could not convert %s to type %s',self.name,s,self._key_type)
            return s

    def connect(self,connection):
        raise NotImplementedError() 
        
    def execute_command(self,cmd):
        action = cmd.action
        method = self.getattr(action)
        method(cmd)
        
def parse_connection(conn):
    return { name: value for name, value in map(lambda c: c.strip().split('=',maxsplit=1), conn.split(';')) }
    
# import remaining files in package to initialize them
my_path = os.path.dirname(__file__)
all = []
for d in os.listdir(my_path):
    if d[-3:] == '.py' and d != '__init__.py':
        importlib.import_module('.'+d[:-3],__package__)
