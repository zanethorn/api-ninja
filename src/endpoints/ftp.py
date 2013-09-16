from ..context import *
from ..log import log
from .tcp import TcpEndpoint
from copy import deepcopy
import http.client, urllib.parse
import io, datetime, gzip, zlib
import email.utils
import traceback

class FtpEndpoint(TcpEndpoint):
    max_request_length = 65536
    
    #STATUS_SUCCESS = 200
    STATUS_LOGGED_IN = 230
    STATUS_WAIT_FOR_PASSWORD = 331
    STATUS_NOT_FOUND = 400
    STATUS_UNAUTHORIZED =530
    
    
    def handle_request(self,connection,client_addr):
        log.debug('handling ftp connection, sending greeting')
        connection.send(b'220 Welcome!\r\n')
        context = self.get_context(connection,client_addr)
        while True:
            try:
                log.debug('processing next command...')
                context.response.data = None
                context.response.status =0
                self.process_context(context)
            except SystemExit:
                break
    
    def parse_request(self,context):
        request = context.request
        response = context.response
        
        raw_input = request._dstream.readline(256)
        if not raw_input:
            raise SystemExit()
            
        raw_input = str(raw_input,'latin-1').strip()
        log.debug('ftp request: %s'%raw_input)
        command = raw_input[:4].upper()
        
        request.command = command
        request.path = raw_input[5:]

        if command == 'QUIT':
            raise SystemExit()
        elif command == 'SYST':
            response.send_error(215,'UNIX Type: L8')
        elif command == 'TYPE':
            context.ftp_mode=request.path[0]
            response.send_error(200, 'Binary mode.')
        elif command == 'PORT':
            l = request.path.split(',')
            request.ftp_address = '.'.join(l[:4])
            request.ftp_port=(int(l[4])<<8)+int(l[5])
            response.send_error(200,'Get port.')

    def find_user(self,context):
        
        request = context.request
        response = context.response
        command = request.command
        log.debug('trying to find ftp user %s'%command)
        if command == 'USER':
            response.send_error(self.STATUS_WAIT_FOR_PASSWORD,'OK.')
        if command == 'PASS':
            context.user = 1
            response.send_error(self.STATUS_LOGGED_IN,'OK.')
            
            
    def format_response(self,context):
        request = context.request
        response = context.response

        out_buffer = io.BytesIO()
        response_line = '%d %s\r\n'%(response.status, response.message)
        response_line = response_line.encode('latin-1','strict')
        out_buffer.write(response_line)
        #traceback.print_stack(limit=2)
        log.debug('returning response %s'%response_line)

        response._dstream.write(out_buffer.getbuffer())
        out_buffer.close()

      