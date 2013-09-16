from .http import HttpEndpoint
import ssl

class HttpsEndpoint(HttpEndpoint):
    certfile = ''
    keyfile = None
    key_password = None
    
    def create_socket(self):
        sock = super().create_socket()
        
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.verify_mode = ssl.CERT_NONE
        context.load_cert_chain(self.certfile,keyfile=self.keyfile,password=self.key_password)
        return context.wrap_socket(sock,server_side=True,do_handshake_on_connect=True, suppress_ragged_eofs=True)
        
    def make_in_file(self,request):
        request._dstream = socket._fileobject(request.connection,'rb',self.in_buffer_size)
        
    def make_out_file(self,response):
        response._dstream = socket._fileobject(request.connection,'wb',self.out_buffer_size)