from ..context import *
from ..log import log
from .tcp import TcpEndpoint
from ..actions import *
from copy import deepcopy
import http.client, urllib.parse
import io, datetime, gzip, zlib
import email.utils


class HttpEndpoint(TcpEndpoint):
    max_request_length = 65536
    
    STATUS_SUCCESS = 200
    STATUS_NO_CONTENT = 204
    STATUS_REDIRECT =302
    STATUS_NOT_MODIFIED =304
    STATUS_BAD_REQUEST =400
    STATUS_UNAUTHORIZED =401
    STATUS_PERMISSION_ERROR =403
    STATUS_NOT_FOUND = 404
    STATUS_ACTION_NOT_ALLOWED = 405
    STATUS_INTERNAL_ERROR  = 500
    
    
    def parse_request(self,context):
        request = context.request
        response = context.response
        
        raw_input = request._dstream.readline(self.max_request_length + 1)
        if len(raw_input) > self.max_request_length:
            response.send_error(414,"Request too large")
            
        if not raw_input:
            return
        
        requestline = str(raw_input,'iso-8859-1')
        requestline = requestline.strip('\r\n')
        
        parts = requestline.split()
        if len(parts) == 3:
            command, path, version = parts
            if version[:5] != 'HTTP/':
                response.send_error(self.STATUS_BAD_REQUEST, "Bad request version (%r)" % version)
        
        request.command = command
        request.full_path = path
        request.version = version
        
        try:
            request.headers = http.client.parse_headers(request._dstream,_class=http.client.HTTPMessage)
        except http.client.LineTooLong:
            response.send_error(self.STATUS_BAD_REQUEST,'Line too long')

        request.uri = urllib.parse.urlparse(path)
        request.path = request.uri.path
        
        request.variables.update(request.headers)
        request.variables.update(request.uri.query)
            
    def format_response(self,context):
        request = context.request
        response = context.response

        if not response.status:
            response.status =self.STATUS_INTERNAL_ERROR
            
        if response.status in range(200,299) and not response.data:
            response.status = self.STATUS_NO_CONTENT
            
        if not response.message:
            response.message = responses[response.status][0]
            
        response.variables['Server'] = 'AnyApi'
        response.variables['Date'] =email.utils.formatdate()
                
        if 'Content-type' not in response.variables:
            response.variables['Content-type'] = response.content_type
            
        data = None
        if request.command != 'HEAD' and response.data:
            data = response.data
            encoding = None
            try:
                encoding = request.variables['Accept-Encoding']
            except KeyError:
                pass
                
            if encoding:
                if 'gzip' in encoding:
                    data = gzip.compress(data)
                    response.variables['Content-Encoding'] = 'gzip'
                elif 'deflate' in encoding:
                    data = zlib.compress(data)
                    response.variables['Content-Encoding'] = 'deflate'
            response.variables['Content-Length'] = len(data)
        
        out_buffer = io.BytesIO()
        response_line = '%s %d %s\r\n'%(request.version, response.status, response.message)
        response_line = response_line.encode('latin-1','strict')
        log.debug('returning response %s'%response_line)
        out_buffer.write(response_line)
        
        for name,value in response.variables.items():
            header_line = '%s: %s\r\n'%(name,value)
            header_line = header_line.encode('latin-1','strict')
            out_buffer.write(header_line)
            
        out_buffer.write('\r\n'.encode('latin-1','strict'))
        
        if data:
            out_buffer.write(data)
        
        response._dstream.write(out_buffer.getbuffer())
        out_buffer.close()
        
    def find_user(self,context):
        pass
        
    def map_action(self,context):
        return action_map[context.request.command]
            
            
action_map= {
    'GET':GET,
    'POST':CREATE,
    'PUT':UPDATE,
    'DELETE':DELETE,
    'OPTIONS':OPTIONS,
    'PATCH':UPDATE
    }
    
        
responses = {
        100: ('Continue', 'Request received, please continue'),
        101: ('Switching Protocols',
              'Switching to new protocol; obey Upgrade header'),

        200: ('OK', 'Request fulfilled, document follows'),
        201: ('Created', 'Document created, URL follows'),
        202: ('Accepted',
              'Request accepted, processing continues off-line'),
        203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
        204: ('No Content', 'Request fulfilled, nothing follows'),
        205: ('Reset Content', 'Clear input form for further input.'),
        206: ('Partial Content', 'Partial content follows.'),

        300: ('Multiple Choices',
              'Object has several resources -- see URI list'),
        301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
        302: ('Found', 'Object moved temporarily -- see URI list'),
        303: ('See Other', 'Object moved -- see Method and URL list'),
        304: ('Not Modified',
              'Document has not changed since given time'),
        305: ('Use Proxy',
              'You must use proxy specified in Location to access this '
              'resource.'),
        307: ('Temporary Redirect',
              'Object moved temporarily -- see URI list'),

        400: ('Bad Request',
              'Bad request syntax or unsupported method'),
        401: ('Unauthorized',
              'No permission -- see authorization schemes'),
        402: ('Payment Required',
              'No payment -- see charging schemes'),
        403: ('Forbidden',
              'Request forbidden -- authorization will not help'),
        404: ('Not Found', 'Nothing matches the given URI'),
        405: ('Method Not Allowed',
              'Specified method is invalid for this resource.'),
        406: ('Not Acceptable', 'URI not available in preferred format.'),
        407: ('Proxy Authentication Required', 'You must authenticate with '
              'this proxy before proceeding.'),
        408: ('Request Timeout', 'Request timed out; try again later.'),
        409: ('Conflict', 'Request conflict.'),
        410: ('Gone',
              'URI no longer exists and has been permanently removed.'),
        411: ('Length Required', 'Client must specify Content-Length.'),
        412: ('Precondition Failed', 'Precondition in headers is false.'),
        413: ('Request Entity Too Large', 'Entity is too large.'),
        414: ('Request-URI Too Long', 'URI is too long.'),
        415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
        416: ('Requested Range Not Satisfiable',
              'Cannot satisfy request range.'),
        417: ('Expectation Failed',
              'Expect condition could not be satisfied.'),
        428: ('Precondition Required',
              'The origin server requires the request to be conditional.'),
        429: ('Too Many Requests', 'The user has sent too many requests '
              'in a given amount of time ("rate limiting").'),
        431: ('Request Header Fields Too Large', 'The server is unwilling to '
              'process the request because its header fields are too large.'),

        500: ('Internal Server Error', 'Server got itself in trouble'),
        501: ('Not Implemented',
              'Server does not support this operation'),
        502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
        503: ('Service Unavailable',
              'The server cannot process the request due to a high load'),
        504: ('Gateway Timeout',
              'The gateway server did not receive a timely response'),
        505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
        511: ('Network Authentication Required',
              'The client needs to authenticate to gain network access.'),
        }