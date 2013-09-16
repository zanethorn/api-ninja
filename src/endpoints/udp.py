from .endpoint import Endpoint

class UdpEndpoint(Endpoint):
    def create_socket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def start_service(self):
        pass # do nothing for a UDP socket
    
    def finalize_request(self,request):
        self.close_request(request)
    
    def close_request(self,request):
        pass # does nothing, no need to close a UDP request
        
    