from ..context import *
from ..log import log
from .tcp import TcpEndpoint
from ..actions import *
from copy import deepcopy
import http.client, urllib.parse
import io, datetime, gzip, zlib
import email.utils
from apininja.data.formatters.html import *


class HttpEndpoint(TcpEndpoint):
    secure_protocol = 'https'
    max_request_length = 65536
    user_database = ''
    default_formatter = HtmlFormatter
    
    action_map= {
        'HEAD':GET,
        'GET':GET,
        'POST':CREATE,
        'PUT':UPDATE,
        'DELETE':DELETE,
        'OPTIONS':OPTIONS,
        'PATCH':UPDATE
        }
    
    STATUS_SUCCESS = 200
    STATUS_NO_CONTENT = 204
    STATUS_REDIRECT =302
    STATUS_NOT_MODIFIED =304
    STATUS_BAD_REQUEST =400
    STATUS_UNAUTHORIZED =401
    STATUS_PERMISSION_ERROR =403
    STATUS_NOT_FOUND = 404
    STATUS_ACTION_NOT_ALLOWED = 405
    STATUS_NOT_ACCEPTABLE = 406
    STATUS_CONFLICT = 409
    STATUS_INTERNAL_ERROR  = 500
    STATUS_NOT_IMPLEMENTED = 501

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
        
        log.debug('%s got request %s',self.name,requestline)
        parts = requestline.split()
        if len(parts) == 3:
            command, path, version = parts
            if version[:5] != 'HTTP/':
                response.send_error(self.STATUS_BAD_REQUEST, "Bad request version (%r)" % version)
            if not command:
                response.send_error(self.STATUS_BAD_REQUEST, "Bad request version (%r)" % version)
                
        request.command = command.upper()
        request.version = version

        try:
            headers = http.client.parse_headers(request._dstream,_class=http.client.HTTPMessage)
        except http.client.LineTooLong:
            response.send_error(self.STATUS_BAD_REQUEST,'Line too long')
            
        for h in headers:
            h = h.lower()
            try:
                var_name = request_header_map[h]
            except KeyError:
                var_name = h
            value = headers[h]
            setattr(request,var_name,value)
            
        # fix header values
        if request.allowed_types:
            request.allowed_types = request.allowed_types.split(',')
        if request.allowed_compression:
            request.allowed_compression = request.allowed_compression.split(',')
        if request.if_modified_since:
            request.if_modified_since = email.utils.parsedate_to_datetime(request.if_modified_since)
        if request.send_date:
            request.send_date = email.utils.parsedate_to_datetime(request.send_date)
        if request.data_length:
            request.data_length = int(request.data_length)
        try:
            request.variables = { p[0]:p[1] for p in map(lambda c: c.strip().split('='),request.cookie.split(';'))}
        except AttributeError:
            pass
                
        request.uri = urllib.parse.urlparse(path)
        request.full_path = request.uri.path.lower()
        request.path = list(filter(lambda i:i,request.full_path.split('/')))
        
        query_parts = request.uri.query.split('&')
        for q in query_parts:
            if q:
                name, val = q.split('=')
                if name[0] == '$':
                    request.options[name[1:]]=val
                else:
                    request.query[name] = val
                    
        #context.variables.update(request.query)
        #context.variables.update(request.options)
                
    def format_response(self,context):
        request = context.request
        response = context.response

        if not response.status:
            response.status =self.STATUS_INTERNAL_ERROR
            
        if response.status in range(200,299) and not response.data:
            response.status = self.STATUS_NO_CONTENT
            
        if not response.message:
            response.message = responses[response.status][0]
            
        response.send_date =email.utils.formatdate()
        if response.allow_actions:
            response.allow_actions = ', '.join([reverse_action_map[i] for i in response.allow_actions])
            
        if response.last_modified:
            response.last_modified = email.utils.format_datetime(response.last_modified)
            
        if request.if_no_match:
            if request.if_no_match == response.data_hash:
                response.status = STATUS_NOT_MODIFIED
                response.data = None
            
        # write response line
        out_buffer = io.BytesIO()
        response_line = '%s %d %s\r\n'%(request.version, response.status, response.message)
        response_line = response_line.encode('latin-1','strict')
        #log.debug('returning response %s'%response_line)
        out_buffer.write(response_line)
        
        # write headers
        log.debug('Writing Headers')
        for var,header in response_header_map.items():
            value = getattr(response,var)
            
            if value:
                header_line = '%s: %s\r\n'%(header,value)
                header_line = header_line.encode('latin-1','strict')
                out_buffer.write(header_line)
                
        # write cookie (if any)
        cookie = ';'.join(map(lambda i: '%s=%s'%i,response.variables.items()))
        if cookie:
            log.debug('Writing Cookies \'%s\'',cookie)
            cookie = 'set-cookie: '+cookie+'\r\n'
            cookie = cookie.encode('latin-1','strict')
            out_buffer.write(cookie)
            
        out_buffer.write('\r\n'.encode('latin-1','strict'))
        
        # write body
        log.debug('Writing Body')
        if request.command != 'HEAD' and response.data:
            out_buffer.write(response.data_stream)
        
        
        #out_buffer.flush()
        # dump everything to output stream
        out_buffer.seek(0)
        buffer =out_buffer.read()
        log.debug('Exporting stream')
        response._dstream.write(buffer)
        response._dstream.flush()
        out_buffer.close()
        log.debug('Closing Buffer')
        
    def find_user(self,context):
        token = None
        try:
            token = context.request.variables['token']
        except KeyError:
            return None
        
        db = self.app.get_database(self.user_database,context)
        users = db.get('users')
        user = users.get_user_by_token(token)
        if user:
            log.debug('Found user %s with token %s',user,token)
        return user
        
    
            
    
request_header_map = {
    'accept':'allowed_types',
    'accept-charset':'allowed_charsets',
    'accept-encoding':'allowed_compression',
    'accept-language':'allowed_language',
    'authorization':'authorization',
    'cache-control':'cache_control',
    'connection':'connection',
    'content-length':'data_length',
    'content-md5':'data_hash',
    'content-type':'mime_type',
    'date':'send_date',
    'expect':'expect',
    'from':'username',
    'host':'host',
    'user-agent':'sender',
    'if-modified-since':'if_modified_since',
    'if-none-match':'if_no_match',
    'te':'compression'
    }
    
response_header_map = {
    'allow_actions':'Allow',
    'cache_control':'Cache-Control',
    'compression':'Content-Encoding',
    'language':'Content-Language',
    'data_length':'Content-Length',
    'alternate_location':'Content-Location',
    'data_hash':'Content-MD5',
    'data_range':'Content-Range',
    'mime_type':'Content-Type',
    'send_date':'Date',
    'data_expires':'Expires',
    'last_modified':'Last-Modified',
    'new_location':'Location',
    'application_string':'Server',
    'data_encoding':'Transfer-Encoding',
    #'connection_handling':'Connection'
    }
    
status_map = {
    'success':(200,'OK'),
    'created':(201,'Created'),
    'no-response':(204,'No Content')
    }
    

    
reverse_action_map= {
    LIST:'GET, HEAD',
    GET:'GET, HEAD',
    CREATE:'POST',
    UPDATE:'PUT',
    DELETE:'DELETE'
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