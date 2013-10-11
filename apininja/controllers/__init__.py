import os, importlib

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
        can_access = self.can_access_resource(resource)
        if not can_access:
            self.response.permission_error()
        
        self.response.allow_actions = self.get_allowed_actions(resource)
        last_modified = self.get_last_modified(resource)
        self.response.last_modified = last_modified
        
        if self.request.if_modified_since and last_modified:
            print(last_modified, self.request.if_modified_since)
            if last_modified <= self.request.if_modified_since:
                self.response.not_modified()
        
        method = self.find_method()

        #args, kwargs = self.map_parameters(method)
        result = method(resource)
        return result
        
    def can_access_resource(self,resource):
        if  self.allow_anonymous or self.context.user:
            return True
        return False
        
    def locate_resource(self, path):
        raise NotImplementedError()
        
    def get_allowed_actions(self,resource):
        raise NotImplementedError()
        
    def get_last_modified(self,resource):
        return None
        
    def format_content(self,content):
        return content
        
    def find_method(self):
        try:
            return getattr(self,self.context.action)
        except AttributeError:
            self.context.response.action_not_allowed()

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
