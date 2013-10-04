import __main__
from .log import *
log.info('Importing namespaces and discovering registered types')

from .helpers import *
from .routing import Route
from .server import SecureServer

from .controllers import ControllerMetaclass
from .endpoints import EndpointMetaclass
from .data.adapters import AdapterMetaclass
from .data.formatters import FormatterMetaclass
from .data.database import DatabaseMetaclass, Database
from .security import User, Users
from .plugins import *
import os, importlib, collections, imp
import time
import smtplib
import json
from copy import copy, deepcopy
from .parser import CommandParser

app_root =  os.getcwd()
my_path = os.path.dirname(__file__)
for f in os.listdir(my_path):
    if os.path.isdir(f):
        importlib.import_module(__package__+'.'+f)

from __addons__ import *

class ApiApplication(Configurable):
    login_path = '/login'
    application_string = 'ApiNinja v. 0.1 (dev)'
    
    def __init__(self):
        super().__init__()
        self.parser = CommandParser(self)
        self.running = False
        
        self.app_root =app_root
        
        self.endpoints = {}
        self.routes = {}
        self.controllers = {}#copy(ControllerMetaclass.known_types)
        self.controller_config ={}
        self.data_adapters = {}
        self.database_config = {}
        self.formatter_config={}
        self.plugins = []
        
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
            
        # we need to configure plugins first due to type-lookup issues
        try:
            plugins = config['plugins']
            self.setup_plugins(plugins)
        except KeyError:
            pass
            
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
        # elif name == 'plugins':
            # pass # plugins should already be registered
        else:
            super()._handle_config_list(name,value)
        
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
            try:
                time.sleep(.1)
            except:
                self.shutdown()
                raise
            
    def shutdown(self):
        for end in self.endpoints.values():
            end.stop()
        self.running = False
        
    def restart(self):
        self.shutdown()
        self.run()
        
    def setup_plugins(self, plugins):
        log.info('Registering plugins:')
        for name, config in plugins.items():
            log.info('Loading plugin %s'%name)
            plugin = importlib.import_module('%s.plugins.%s'%(__package__,name))
            try:
                load = getattr(plugin,'load')
                load(config)
            except AttributeError:
                pass
        
    def setup_endpoints(self, config):
        log.info('Setting up Endpoints:')
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
            log.info('Registering Endpoint %s',name)
            self.endpoints[name] = endpoint
        
    def setup_routes(self, config):
        routes = collections.OrderedDict()
        for r in config:
            try:
                name = r['name']
            except KeyError:
                raise ValueError('Name must be specified for routes')
                
            if name in self.routes:
                raise ValueError('Route names must be unique')
                
            route = Route(r)
            routes[name] = route
        self.routes = routes
            
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
                    
            log.info('Registering Controllers %s',name)
            self.controller_config[name] = c
        
    def map_route(self,request):
        for r in self.routes.values():
            v = r.match(request)
            if v is not None:
                return r, v
        return None, None
                
    def get_controller(self,name, context):
        cls = None
        if name:
            try:
                cls= self.controllers[name]
            except KeyError:
                try:
                    cls =  ControllerMetaclass.known_types[name]
                except KeyError:
                    pass
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
                    
            log.info('Registering Data Adapter %s',name)
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
                
            self.database_config[name] = c
                
    def get_database(self,name,context):
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
        
        
    def get_formatter(self,context, response=True):
        types = FormatterMetaclass.known_types.values()
        formats = []
        if response:
            if context.response.mime_type:
                formats = [ context.response.mime_type ]
            else:
                try:
                    f = context.request.variables['format']
                    if f:
                        formats = map_format(f)
                except KeyError:
                    pass
                
                if not formats:
                    formats = context.request.allowed_types
        else:
            formats = [ context.request.mime_type ]        
        
        #log.debug('Finding formatter for %s',formats)
        format_type = None
        for t in formats:
            for f in types:
                if t in f.mime_types:
                    format_type = f
                    break
            if format_type:
                break
        if not format_type:
            format_type= context.endpoint.default_formatter
        config = None
        try:
            config = self.formatter_config[format_type.name]
        except KeyError:
            pass
        if response:
            context.response.mime_type = format_type.mime_types[0]
        formatter = format_type(context,config)
        return formatter
        
    def send_mail(self,to_addr,from_addr,message):
        server = smtplib.SMTP('localhost')
        server.set_debuglevel(1)
        server.sendmail(from_addr, to_addr, message)
        server.quit()
        
if __name__ == '__main__':
    app = ApiApplication()
    app.run()