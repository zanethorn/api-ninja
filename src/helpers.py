
class Configurable():
    def __init__(self,config=None):
        if config:
            self._configure(config)
    
    def _configure(self,config):
        for k,v in config.items():
            if isinstance(v,dict):
                self._handle_dict(k,v)
            elif isinstance(v,list):
                self._handle_list(k,v)
            else:
                self._handle_value(k,v)
                
    def _handle_value(self,name,value):
        setattr(self,name,value)
        
    def _handle_dict(self,name,value):
        pass
        
    def _handle_list(self,name,value):
        pass
        