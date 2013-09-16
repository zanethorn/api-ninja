import http.server
import socketserver, socket
import ssl
from .config import config
from .log import *
from .context import *
from .httpexception import HttpException

server = None

class RouteHandler(http.server.BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def __init__(self, request, client_address, server):
        self.app = server.app
        super().__init__(request, client_address, server)
        
    def handle_one_request(self):
        response = ResponseContext()
        request = RequestContext()
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                raise HttpException(414)
            if not self.raw_requestline:
                self.close_connection = 1
                return
            if not self.parse_request():
                # An error code has been sent, just exit
                return

            path = self.path
            log.info('beginning request for %s' % path)
            request = RequestContext(path,self.command,self.headers,self.rfile)

            route = self.app.find_route(path)
            if not route:
                raise HttpException(404)
            args = route.get_args(path)
            
            # find controller
            try:
                controller_name = args['controller']
                del args['controller']
            except KeyError:
                controller_name = route.controller
            if not controller_name:
                raise HttpException(404)
                
            # find action  
            try:
                action_name = args['action']
                del args['action']
            except KeyError:
                action_name = route.action
            if not action_name:
                raise HttpException(404)
                
            controller = self.app.find_controller(controller_name)
            if not controller:
                raise HttpException(404)
                
            # finish setting up context
            ctrl = controller(self.app)
            context = ExecutionContext(request,response,controller,action_name)
            ctrl.execute(context)
                
        except HttpException as ex:
            response.status = ex.status
            message = ex.message
            if not message:
                message = self.responses[1]
            response.data = response
        except socket.timeout as e:
            #a read or a write timed out.  Discard this connection
            log.error("Request timed out: %r", e)
            self.close_connection = 1
        finally:
            finalize_request(response)
            
    def finalize_request(self,response):
        if response.status in range(200,299) and not response.data:
            response.status = 204
        self.send_head(response)
        
        if response.data:
            self.send_body(response)
        self.wfile.flush() #actually send the response if not already done.
            
    def send_head(self,response):
        self.send_response(self.status)
        for header,value in response.headers.items():
            self.send_header(header,value)
        self.end_headers()
    
try:
    forking = config['HTTP'].getboolean('fork_request')
    assert os.fork
except (KeyError,AttributeError):
    forking = False
    
if forking:
    class ParallelServer(socketserver.ForkingMixIn,http.server.HTTPServer): pass
else:
    class ParallelServer(socketserver.ThreadingMixIn,http.server.HTTPServer): pass

#class ParallelServer(http.server.HTTPServer): pass
    
class SecureServer(ParallelServer):
    def __init__(self,app):
        super().__init__()
        self.app = app
    
        global server
        
        # grab information from config.ini file
        host = config['HTTP']['host_name']
        port = int(config['HTTP']['host_port'])
        address = (host,port)
        
        super().__init__(address,RouteHandler)
        try:
            certfile = os.path.join(os.getcwd(),config['HTTP']['certificate'])
            try:
                keyfile =os.path.join(os.getcwd(),config['HTTP']['keyfile'])
            except KeyError:
                keyfile = None
            try:
                password =config['HTTP']['ssl_password']
            except KeyError:
                password = None
                
            print(certfile,keyfile)
           
            
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            context.verify_mode = ssl.CERT_NONE
            context.load_cert_chain(certfile,keyfile=keyfile,password=password)
                # self.socket,
                # certfile=certfile, 
                # keyfile=keyfile,
                # server_side=True,
                # cert_reqs = ssl.CERT_NONE,
                # ssl_version = ssl.PROTOCOL_TLSv1,
                # ca_certs = None,
                # do_handshake_on_connect = True, 
                # suppress_ragged_eofs=True, 
                # ciphers=None
                # )
            self.socket = context.wrap_socket(self.socket,server_side=True,do_handshake_on_connect=True, suppress_ragged_eofs=True)
            # self.socket.keyfile = keyfile
            # self.socket.certfile = certfile
            # self.socket.cert_reqs = ssl.CERT_NONE
            # self.socket.ssl_version = ssl.PROTOCOL_TLSv1
            # self.socket.ca_certs = None
            # self.socket.ciphers=None
            
        except KeyError:
            # SSL information is not defined, use HTTP only
            log.warning('Could not set SSL, running in HTTP mode only')
            
        # set the global server
        server = self
        
    def setup(self):
        self.connection = self.request
        if self.timeout is not None:
            self.connection.settimeout(self.timeout)
        if self.disable_nagle_algorithm:
            self.connection.setsockopt(socket.IPPROTO_TCP,
                                       socket.TCP_NODELAY, True)
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)
        
    def serve_forever(self):
        log.info('Starting server NOW!')
        super().serve_forever()
        
def run():
    server  = SecureServer()
    server.serve_forever()
        
        
if __name__ == '__main__':
    run()