import os, importlib
import gzip, zlib, bz2, lzma
#from .controller import *
from apininja.log import log
from apininja.helpers import *
log.info('Initializing apininja.controllers namespace')

import inspect
from copy import deepcopy

def verbs(*args):
    def _verbs(fcn):
        fcn.verbs = args
        return fcn
    return _verbs

class ControllerMetaclass(SelfRegisteringType):
    extension = 'Controller'

class Controller(Configurable, metaclass=ControllerMetaclass):
    allow_anonymous = False
    name = ''

    def __init__(self,app,context,config=None):
        super().__init__(config)
        self.app = app
        self.context = context
        self.name = type(self).__name__.replace('Controller','')
        
    @property
    def context(self):
        return self._context
        
    @property
    def request(self):
        return self.context.request
        
    @property
    def response(self):
        return self.context.response
        
    @context.setter
    def context(self,value):
        self._context = value
        
    def execute(self):
        resource = self.locate_resource(self.request.path)
        self.response.allow_actions = self.get_allowed_actions(resource)
        
        method = self.find_method()

        #args, kwargs = self.map_parameters(method)
        result = method(resource)
        
        result = self.format_content(result)
        self.response.data = self.compress_content(result)
        return result
        
    def locate_resource(self, path):
        raise NotImplementedError()
        
    def get_allowed_actions(self,resource):
        raise NotImplementedError()
        
    def compress_content(self,data):
        if self.request.allowed_compression:
            for ctype in self.request.allowed_compression:
                try:
                    compressor = compressors[ctype]
                    encoded = compressor.encode(data)
                    self.response.compression = ctype
                    return encoded
                except KeyError:
                    pass
        return data
        
    def format_content(self,content):
        return content
        
    def find_method(self):
        try:
            return getattr(self,self.context.action)
        except AttributeError:
            self.context.response.action_not_allowed()

    # def map_parameters(self, method):
        # variables = self.context.request.variables
        # spec = inspect.getfullargspec(method)
        # used = []
        # args = ()
        # kwargs = {}
        
        # for a in spec.args[1:]:
            # # skip the "self" argument since we are bound to a class
            # args += (variables[a], )
            # used.append(a)

        # if spec.varargs:
            # args += tuple(variables[spec.varargs])
            # used.append(spec.varargs)

        # for kw in spec.kwonlyargs:
            # try:
                # kwargs[kw] = variables[kw]
                # used.append(kw)
            # except KeyError:
                # pass

        # # pass remaining parameters to kwargs, if allowed
        # if spec.varkw:
            # for k,v in variables.items():
                # if k not in used:
                    # kwargs[k] = v
        # return (args, kwargs)
            
            
    def list(self, resource):
        self.response.action_not_allowed()
        
    def get(self, resource):
        self.response.action_not_allowed()
        
    def create(self, resource):
        self.response.action_not_allowed()
        
    def update(self, resource):
        self.response.action_not_allowed()
        
    def delete(self, resource):
        self.response.action_not_allowed()

compressors = {
    'lzma':lzma,
    'gzip':gzip,
    'deflate':zlib,
    'bzip2':bz2
    }
        
# import remaining files in package to initialize them
my_path = os.path.dirname(__file__)
all = []
for d in os.listdir(my_path):
    if d[-3:] == '.py' and d != '__init__.py':
        importlib.import_module('.'+d[:-3],__package__)

# import application-specific controllers from directory
app_path = os.getcwd()
ctrl_path = os.path.join(app_path,'controllers')
__path__.append(ctrl_path)
if os.path.exists(ctrl_path):
    for d in os.listdir(ctrl_path):
        if d[-3:] == '.py' and d != '__init__.py':
            importlib.import_module('.'+d[:-3],__package__)
