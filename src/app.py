from .helpers import *
from .routing import Route
from .server import SecureServer
from .controllers import *
from .controllers import controllers
from .log import *
from .endpoints import *
from .endpoints import protocols
import os, importlib
import time
import json
from copy import copy, deepcopy

application_string = 'AnyApi v'

class ApiApplication(Configurable):
    login_path = '/login'

    def __init__(self):
        super().__init__()
        self.running = False
        
        self.app_root = os.getcwd()
        self.endpoints = {}
        self.routes = {}
        self.controllers = copy(controllers)
        self.controller_config ={}
        
        self.configure()
        
    def configure(self):
        path = os.path.join(self.app_root,'config.json')
        config = None
        try:
            file = open(path)
            #print(file.read())
            config = json.load(file)
        finally:
            file.close()
        self._configure(config)
        
    def _handle_list(self,name,value):
        if name == 'controllers':
            self.setup_controllers(value)
        elif name == 'endpoints':
            self.setup_endpoints(value)
        elif name == 'routes':
            self.setup_routes(value)
        else:
            raise AttributeError(name)
        
    def run(self):
        log.info('Starting Application Server')
        if len(self.endpoints) == 0:
            raise RuntimeError('No endpoints configured!')
        if len(self.routes) == 0:
            raise RuntimeError('No routes configured!')
            
        for end in self.endpoints.values():
            end.start()

        self.running = True
        while self.running:
            time.sleep(1)
            
            
    def shutdown(self):
        for end in self.endpoints:
            end.stop()
        self.running = False
        
    def setup_endpoints(self, config):
        log.info('Setting up Endpoints')
        for c in config:
            try:
                name = c['name']
            except KeyError:
                raise ValueError('Name must be specified for endpoints')
                
            if name in self.endpoints:
                raise ValueError('Endpoint names must be unique')
                
            try:
                protocol = c['protocol']
            except KeyError:
                raise ValueError('Protocol must be specified for endpoint %s'%name)
                
            try:
                end_cls = protocols[protocol]
            except KeyError:
                raise ValueError('protocol %s not found'%protocol)
                
            endpoint = end_cls(self,c)
            self.endpoints[name] = endpoint
        
    def setup_routes(self, config):
        for r in config:
            try:
                name = r['name']
            except KeyError:
                raise ValueError('Name must be specified for routes')
                
            if name in self.routes:
                raise ValueError('Route names must be unique')
                
            route = Route(r)
            self.routes[name] = route
            
    def setup_controllers(self,config):
        for c in config:
            try:
                name = c['name']
            except KeyError:
                raise ValueError('Name must be specified for controllers')
                
            if name in self.controllers:
                raise ValueError('Controller names must be unique')
                
            try:
                map_to = c['map_to']
                self.controllers[name] = controllers[map_to]
            except KeyError:
                try:
                    self.controllers[name] = controllers[name]
                except KeyError:
                    raise ValueError('Controllers %s did not specifiy a mapping type (map_to) and no known controller type matched name'%name)
                    
            self.controller_config[name] = c
        
    def map_route(self,request):
        for r in self.routes.values():
            
            if r.is_match(request):
                return r
                
    def find_controller(self,context):
        c_name = ''
        cls = None
        if context.route.controller:
            c_name = context.route.controller
        else:
            try:
                c_name = context.request.variables['controller']
            except KeyError:
                pass
        
        if c_name:
            try:
                cls= self.controllers[c_name]
            except KeyError:
                pass
        if cls:
            config = None
            try:
                config = self.controller_config[c_name]
            except KeyError:
                pass
            controller =  cls(self,context,config)
            return controller
        return None