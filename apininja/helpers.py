import os, importlib
from apininja.log import log

class Configurable():
    _t = ''
    
    def __init__(self,config=None):
        if config is not None:
            self._configure(config)
            if not self._t:
                self._t = type(self).__name__
    
    def _configure(self,config):
        self._config = config
        for k,v in config.items():
            if isinstance(v,dict):
                self._handle_config_dict(k,v)
            elif isinstance(v,list):
                self._handle_config_list(k,v)
            else:
                self._handle_config_value(k,v)
                
    def _handle_config_value(self,name,value):
        setattr(self,name,value)
        
    def _handle_config_dict(self,name,value):
        setattr(self,name,value)
        
    def _handle_config_list(self,name,value):
        setattr(self,name,value)
        
def islambda(obj):
    return isinstance(obj, type(lambda: None)) and obj.__name__ == '<lambda>'
    
class SelfRegisteringType(type):
    extension = ''
    known_types = None
    
    def __new__(meta,name,bases,dict):
        if not meta.known_types:
            meta.known_types = {}
        
        cls = type.__new__(meta,name,bases,dict)
        if name != meta.extension:
            n = name.replace(meta.extension,'').lower()
            cls.name = n
            log.info('Found %s Type %s',meta.extension,n)
            meta.known_types[n]= cls
        return cls
        
def bootstrap_namespace(file):
    my_path = os.path.dirname(file)
    all = []
    for d in os.listdir(my_path):
        if os.path.isdir(d):
            all.append(d)
        elif d[-3:] == '.py' and d != file and d != '__init__.py':
            all.append(d)
    return all