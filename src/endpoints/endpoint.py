import os, time, socket, threading
from ..helpers import *
from ..log import log
from ..context import *
import traceback, inspect

protocols = {}

class EndpointMetaclass(type):
    def __new__(meta,name,bases,dict):
        cls = type.__new__(meta,name,bases,dict)
        if name != 'Endpoint':
            n = name.replace('Endpoint','').lower()
            log.debug('Found Protocol %s'%n)
            protocols[n] = cls
        return cls

class Endpoint(Configurable, metaclass = EndpointMetaclass):
    address = 'localhost'
    port = 80
    name = ''
    protocol = ''
    in_buffer_size = -1
    out_buffer_size = 0
    
    # status constants, override for specific protocols
    STATUS_SUCCESS = 0
    STATUS_NOT_FOUND = 0
    STATUS_REDIRECT =0
    STATUS_ACTION_NOT_ALLOWED = 0
    STATUS_UNAUTHORIZED =0 
    STATUS_PERMISSION_ERROR =0 
    STATUS_BAD_REQUEST =0
    STATUS_INTERNAL_ERROR =0
    STATUS_NOT_MODIFIED =0

    def __init__(self,app, config=None):
        if self.__class__ == Endpoint:
            raise TypeError('Endpoint is abstract')
        super().__init__(config)
        self.app = app
        self._running = False
        self.workers = []
        self.server_address = (self.address,self.port)
        
    @property
    def running(self):
        return self._running

    def start(self):
        if self.app.use_forking:
            self._fork_start()
        else:
            self._thread_start()
            
    def stop(self):
        self._running = False
        self.close_service()
        log.info('Endpoint %s stopped'%self.name)
        
    def create_socket(self):
        raise NotImplementedError()
        
    def handle_connection(self):
        try:
            connection,client_addr = self.accept_connection()  
        except socket.error:
            return
 
        try:
            log.debug('%s recieved a request from %s'%(self.name,client_addr))
            self._spawn_worker(connection,client_addr)
        except Exception as ex:
            self.handle_error(connection,client_addr,ex)
            self.finalize_connection(connection)
            
        return True
            
    def accept_connection(self):
        return self.socket.accept()
        
    def finalize_connection(self,request):
        raise NotImplementedError()
        
    def close_connection(self,request):
        raise NotImplementedError()
        
    def close_service(self):
        log.info('Endpoint %s closing down'%self.name)
        self.socket.close()
        
    def start_service(self):
        raise NotImplementedError()
        
    def handle_request(self,connection,client_addr):
        context = self.get_context(connection,client_addr)
        self.process_context(context)
        
    def get_context(self,connection,client_addr):
        request = RequestContext(self)
        request.client = client_addr
        request.connection = connection
        
        response = ResponseContext(self)
        response.connection = connection
        
        context = ExecutionContext(request,response)
        return context
        
    def process_context(self,context):
        request = context.request
        response = context.response
        
        try:
            self.make_in_file(request)
            self.make_out_file(response)
            
            self.parse_request(context)
            
            if not context.user:
                self.find_user(context)
            
            context.route = self.find_route(context)
            
            context.controller = self.find_controller(context)
            try:
                del request.variables['controller']
            except KeyError:
                pass

            context.action = self.map_action(context)
            try:
                del request.variables['action']
            except KeyError:
                pass

            context.method = self.find_method(context)
            context.parameters = self.map_parameters(context)
            context.response.data = self.execute_method(context)

            if response.status == 0:
                raise RuntimeError('Success Status not implemented!')
                
        except StopExecutionException:
            #traceback.print_last(limit=3)
            log.warning('endpoint stopped with %d'%response.status)
        finally:
            self.format_response(context)
            if not response._dstream.closed:
                try:
                    response._dstream.flush()
                except socket.error:
                    # An final socket error may have occurred here, such as
                    # the local error ECONNABORTED.
                    pass
            request._dstream.close()
            response._dstream.close()
            
    def find_user(self,context):
        raise NotImplementedError()
            
    def parse_request(self,context):    
        raise NotImplementedError()
        
    def format_response(self,context):
        raise NotImplementedError()
        
    def find_route(self,context):
        route = self.app.map_route(context.request)
        if not route:
            context.response.not_found('no route found')
        
        log.debug('%s using route %s'%(self.name,route.name))
        context.route = route
        context.request.variables.update(route.get_variables(context.request.path))
        return route
            
    def find_controller(self,context):
        controller = self.app.find_controller(context)
        if not controller:
            context.response.not_found('no controller found')
            
        log.debug('%s using controller %s'%(self.name,context.route.name))
        return controller
        
    def map_action(self,context):
        raise NotImplementedError()
        
    def find_method(self,context):
        try:
            return getattr(context.controller,context.action)
        except AttributeError:
            context.response.action_not_allowed()
            
    def map_parameters(self,context):
        variables = context.request.variables
        spec = inspect.getfullargspec(context.method)
        used = []
        args = ()
        kwargs = {}
        
        for a in spec.args[1:]:
            # skip the "self" argument since we are bound to a class
            args += (variables[a], )
            used.append(a)

        if spec.varargs:
            args += tuple(variables[spec.varargs])
            used.append(spec.varargs)

        for kw in spec.kwonlyargs:
            try:
                kwargs[kw] = variables[kw]
                used.append(kw)
            except KeyError:
                pass

        # pass remaining parameters to kwargs, if allowed
        if spec.varkw:
            for k,v in variables.items():
                if k not in used:
                    kwargs[k] = v
        return (args, kwargs)
        
    def execute_method(self,context):
        args = context.parameters[0]
        kwargs = context.parameters[1]
        result = context.method(*args,**kwargs)
        if result and not context.response.status:  
                context.response.status = self.STATUS_SUCCESS
        return result
            
    def handle_error(self,request,client_addr,error):
        tb = traceback.format_exc()
        log.error('%s from client %s'%(tb,client_addr))
        
    def make_in_file(self,request):
        request._dstream = request.connection.makefile('rb',self.in_buffer_size)
        
    def make_out_file(self,response):
        response._dstream = response.connection.makefile('wb',self.out_buffer_size)
            
    def _fork_start(self):
        try:
            # try to fork the process first (UNIX systems)
            pid = os.fork()
            if pid:
                # this is the parent process
                self.child_id = pid
            else:
                # this is the child process which actually does the work
                try:
                    self._start()
                    os.exit(0)
                except:
                    os.exit(1)
        except AttributeError:
            # thread the process
            self._thread_start()
            
    def _thread_start(self):
        thread = threading.Thread(target=self._start)
        thread.start()
        self.child_id = thread.ident
            
    def _start(self):
        self.socket = self.create_socket()
        self.start_service()
        self._running = True
        log.info('Endpoint %s started at %s'%(self.name,self.server_address))
        self._run_loop()
        
    def _spawn_worker(self,connection,client_addr):
        if self.app.use_forking:
            self._fork_worker(connection,client_addr)
        else:
            self._thread_worker(connection,client_addr)
        
    def _fork_worker(self,connection,client_addr):
        try:
            pid = os.fork()
            if pid:
                # we are running the parent process
                self.child_processes.append(pid)
                self.close_request(connection)
            else:
                # we are running the child process
                pid = os.getpid()
                status =0
                try:
                    self.handle_request(connection,client_addr)
                except Exception as ex:
                    status = 1
                    self.handle_error(connection,client_addr,ex)
                finally:
                    self.workers.remove(pid)
                    os._exit(status)
        except:
            self._thread_worker(connection,client_addr)
            
    def _thread_worker(self,connection,client_addr):
        thread_id = 0
        def run_worker(connection,client_addr):
            try:
                self.handle_request(connection,client_addr)
            except Exception as ex:
                self.handle_error(connection,client_addr,ex)
            finally:
                self.finalize_connection(connection)
                try:
                    self.workers.remove(thread_id)
                except KeyError:
                    pass
        
        thread = threading.Thread(target=run_worker,args=(connection,client_addr))
        thread.daemon = False
        thread.start()
        thread_id = thread.ident
        self.workers.append(thread_id)
            
    def _run_loop(self):
        try:
            while self._running:
                while self.handle_connection():
                    pass
                time.sleep(.1)
        except:
            self.stop()
            raise