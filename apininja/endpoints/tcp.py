from apininja.endpoints import Endpoint
from apininja.log import log
import socket

class TcpEndpoint(Endpoint):
    socket_timeout = None

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(0)
        return sock
        
    def start_service(self):
        self.socket.bind(self.server_address)
        self.socket.listen(10)
        
    def finalize_connection(self,connection):
        try:
            connection.shutdown(socket.SHUT_WR)
            pass
        except socket.error:
            pass
        finally:
            self.close_connection(connection)
        
    def close_connection(self,connection):
        connection.close()
        pass
    