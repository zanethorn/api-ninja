from .log import *
log.info('Importing namespaces and discovering registered types')

from .helpers import *
from .routing import Route
from .server import SecureServer

from .controllers import ControllerMetaclass
from .endpoints import EndpointMetaclass
from .data.adapters import AdapterMetaclass
from .data.database import DatabaseMetaclass, Database
from .security import User, Users
import os, importlib
import time
import json
from copy import copy, deepcopy
from .parser import CommandParser

my_path = os.path.dirname(__file__)
for f in os.listdir(my_path):
    if os.path.isdir(f):
        importlib.import_module(__package__+'.'+f)


for d in os.listdir(my_path):
    if d == 'bootstrap.py': continue
    if os.path.isdir(d):
        importlib.import_module(__package__+'.'+d)

class ApiApplication(Configurable):
    login_path = '/login'
    application_string = 'ApiNinja v. 0.1 (dev)'

    def __init__(self):
        super().__init__()
        self.parser = CommandParser(self)
        self.running = False
        
        self.app_root = os.getcwd()
        self.endpoints = {}
        self.routes = {}
        self.controllers = copy(ControllerMetaclass.known_types)
        self.controller_config ={}
        self.data_adapters = {}
        self.database_config = {}
        
        self.configure()
        
    def configure(self):
        log.info('Configuring Application Instance')
        path = os.path.join(self.app_root,'config.json')
        config = None
        try:
            file = open(path)
            #print(file.read())
            config = json.load(file)
        finally:
            file.close()
        self._configure(config)
        
    def _handle_config_list(self,name,value):
        if name == 'controllers':
            self.setup_controllers(value)
        elif name == 'endpoints':
            self.setup_endpoints(value)
        elif name == 'routes':
            self.setup_routes(value)
        elif name == 'databases':
            self.setup_databases(value)
        elif name == 'adapters':
            self.setup_adapters(value)
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
        
        #print('ApiNinja Command Shell')
        while self.running:
            # i = input('>>')
            # o = self.parser.process_command(i)
            # print(o)
            time.sleep(.1)
        
            
    def shutdown(self):
        for end in self.endpoints.values():
            end.stop()
        self.running = False
        
    def restart(self):
        self.shutdown()
        self.run()
        
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
                end_cls = EndpointMetaclass.known_types[protocol]
            except KeyError:
                raise ValueError('protocol %s not found'%protocol)
                
            endpoint = end_cls(self,c)
            log.debug('Registering Endpoint %s',name)
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
        log.info('Setting up Controllers')
        for c in config:
            try:
                name = c['name']
            except KeyError:
                raise ValueError('Name must be specified for controllers')
                
            if name in self.controllers:
                raise ValueError('Controller names must be unique')
                
            try:
                map_to = c['map_to']
                self.controllers[name] = ControllerMetaclass.known_types[map_to]
            except KeyError:
                try:
                    self.controllers[name] = ControllerMetaclass.known_types[name]
                except KeyError:
                    raise ValueError('Controller %s did not specifiy a mapping type (map_to) and no known controller type matched name'%name)
                    
            log.debug('Registering Controllers %s',name)
            self.controller_config[name] = c
        
    def map_route(self,request):
        for r in self.routes.values():
            if r.is_match(request):
                return r
                
    def get_controller(self,name, context):
        if name:
            try:
                cls= self.controllers[name]
            except KeyError:
                try:
                    cls = controllers[name]
                except KeyError:
                    cls = None
        if cls:
            config = None
            try:
                config = self.controller_config[name]
            except KeyError:
                pass
            controller = cls(self,context,config = config)
            return controller
        return None
        
    def setup_adapters(self,config):
        log.info('Setting up Database Adapters')
        for c in config:
            try:
                name = c['name']
            except KeyError:
                raise ValueError('Name must be specified for adapters')
                
            try:
                map_to = c['map_to']
                adapter_cls = adapters[map_to]
            except KeyError:
                try:
                    adapter_cls = adapters[name]
                except KeyError:
                    raise ValueError('Adapter %s did not specifiy a mapping type (map_to) and no known data adapter type matched name'%name)
                    
            log.debug('Registering Data Adapter %s',name)
            self.data_adapters[name] = adapter_cls(c)
            
    def setup_databases(self,config):
        log.info('Setting up Databases')
        for c in config:
            try:
                name = c['name']
            except KeyError:
                raise ValueError('Name must be specified for databases')
                
            if name in self.database_config:
                raise ValueError('Database names must be unique')
                
            try:
                adapter = c['adapter']
            except KeyError:
                raise ValueError('Adapter must be specified for databases')
                
            try:
                adapter = c['connection']
            except KeyError:
                raise ValueError('Connection must be specified for databases')
                
            #log.debug('Registering Database %s with %s',name,c)
            self.database_config[name] = c
                
    def get_database(self,name,context = None):
        try:
            config = self.database_config[name]
        except KeyError:
            return None
        
        adapter_name = config['adapter']
        try:
            adapter = self.data_adapters[adapter_name]
        except KeyError:
            try:
                adapter = AdapterMetaclass.known_types[adapter_name]()
            except KeyError:
                raise ValueError('Adapter %s could not be found for database %s'%(adapter_name,name))
            
        try:
            db_type_name = config['type']
            try:
                db_type = DatabaseMetaclass.known_types[db_type_name]
            except KeyError:
                raise ValueError('Could not find database type %s'%db_type_name)
        except KeyError:
            db_type = Database
            
        db = db_type(self,adapter,config,context)
        return db