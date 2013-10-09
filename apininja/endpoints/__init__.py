import os, time, socket, threading
import traceback, inspect
from apininja.helpers import *
from apininja.log import log
from apininja.context import *
from apininja.security import root, unauthorized
log.info('Initializing apininja.endpoints namespace')


class EndpointMetaclass(SelfRegisteringType):
    extension = 'Endpoint'

class Endpoint(Configurable, metaclass = EndpointMetaclass):
    
    
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
    STATUS_NOT_IMPLEMENTED = 0

    def __init__(self,app, config=None):
        if self.__class__ == Endpoint:
            raise TypeError('Endpoint is abstract')
        self.address = 'localhost'
        self.port = 80
        self.name = ''
        self.protocol = ''
        self.in_buffer_size = -1
        self.out_buffer_size = 0
        self.action_map = {}
        self.default_formatter = None
            
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
        
    def finalize_connection(self,connection):
        self.close_connection(connection)
        
    def close_connection(self,connection):
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
        context.endpoint = self
        return context
        
    def process_context(self,context):
        request = context.request
        response = context.response
        
        try:
            self.make_in_file(request)
            self.make_out_file(response)
            
            self.parse_request(context)
            context.action = self.map_action(context)
            log.info('%s handling request for %s:%s'%(self.name,context.action,request.path))
            
            if not context.user:
                u = self.find_user(context)
                if u:
                    context.user = u
            
            context.route = self.find_route(context)
            context.controller = self.find_controller(context)
            
            context.response.data  = context.controller.execute()
            if not context.response.status:  
                context.response.status = self.get_success_status(context)

            if response.status == 0:
                raise RuntimeError('Success Status not implemented!')
                
        except StopExecutionException:
            #traceback.print_last(limit=3)
            log.warning('Endpoint %s stopped with %d',self.name,response.status)
        except Exception as ex:
            # if __debug__:
                # raise
            log.error('Endpoint %s encoutered error %s',self.name, ex)
            traceback.print_exc()
            if isinstance(ex,NotImplementedError):
                response.status = self.STATUS_NOT_IMPLEMENTED
            else:
                response.status = self.STATUS_INTERNAL_ERROR
            response.message = str(ex)
            response.data = None
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
            
    def get_success_status(self,context):
        return self.STATUS_SUCCESS
            
    def find_user(self,context):
        raise NotImplementedError()
            
    def parse_request(self,context):    
        raise NotImplementedError()
        
    def format_response(self,context):
        raise NotImplementedError()
        
    def find_route(self,context):
        route, variables = self.app.map_route(context.request)
        if not route:
            context.response.not_found('no route found')
        
        log.debug('%s using route %s'%(self.name,route.name))
        context.route = route
        #route_variables = route.get_variables(context.request.full_path)
        context.request.variables.update(variables)
        if 'path' in variables:
            context.request.path = variables['path']
        return route
            
    def find_controller(self,context):
        name = ''
        if context.route.controller:
            name = context.route.controller
        else:
            try:
                name = context.variables['controller']
            except KeyError:
                pass
        controller = self.app.get_controller(name,context)
        if not controller:
            context.response.not_found('no controller found')
        controller.context = context
        log.debug('%s using controller %s'%(self.name,context.route.name))
        return controller
        
    def map_action(self,context):
        log.debug('%s finding action for \'%s\'',self.name,context.request.command)
        try:
            return self.action_map[context.request.command]
        except KeyError:
            context.response.action_not_allowed()
            
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
                # if __debug__:
                    # raise
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

# import remaining files in package to initialize them
my_path = os.path.dirname(__file__)
all = []
for d in os.listdir(my_path):
    if d[-3:] == '.py' and d != '__init__.py':
        importlib.import_module('.'+d[:-3],__package__)