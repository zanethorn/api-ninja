from ..httpexception import HttpException
from ..log import log
from ..helpers import *
import inspect
from copy import deepcopy

controllers = {}



def verbs(*args):
    def _verbs(fcn):
        fcn.verbs = args
        return fcn
    return _verbs

class ControllerMetaclass(type):
    def __new__(meta,name,bases,dict):
        cls = type.__new__(meta,name,bases,dict)
        if name != 'Controller':
            n = name.replace('Controller','').lower()
            log.debug('Found Controller %s'%n)
            controllers[n] = cls
        return cls

class Controller(Configurable, metaclass=ControllerMetaclass):
    allow_anonymous = False

    def __init__(self,app,context,config=None):
        super().__init__(config)
        self.app = app
        self.context = context
        self.request = context.request
        self.response = context.response
        self.name = type(self).__name__.replace('Controller','')

    def list(self):
        self.action_not_allowed()
        
    def get(self):
        self.action_not_allowed()
        
    def create(self):
        self.action_not_allowed()
        
    def update(self):
        self.action_not_allowed()
        
    def delete(self):
        self.action_not_allowed()
