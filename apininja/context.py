import traceback
import hashlib, base64, hmac
from apininja.log import log
from apininja.data.formatters import *
from apininja.data import *

class StopExecutionException(Exception):
    pass

class RequestContext():
    protocol = ''
    endpoint = None
    client = None
    raw_request = None
    path = ''
    version=''
    command = ''
    content_type= None
    query = {}
    options = {}
    cookies = {}
    
    data_length = 0
    compression = None
    allowed_types = []
    allowed_charsets = []
    allowed_compression = []
    allowed_language = []
    authorization = None
    cache_control = None
    connection = None
    data_hash = None
    mime_type = None
    send_date = None
    expect = None
    username = None
    host = None
    sender = None
    if_modified_since = None
    if_no_match = None
    
    def __init__(self,endpoint):
        self.endpoint = endpoint
        self.protocol = endpoint.protocol
        self.app = endpoint.app
        self._data = None
    
    @property
    def data(self):
        if self._data:
            return self._data
        if not self.data_length:
            return None
        
        if not self._data and self.data_length:
            raw = self._dstream.read(self.data_length)
            
            if self.compression:
                log.debug('decompressing data stream with %s',self.compression)
                raw = decompress_data(self.context,raw)
                
            formatter = get_formatter(self.context,False)
            if formatter:
                data = formatter.decode(raw)
            else:
                data = raw
                
            if isinstance(data,dict):
                try:
                    t = data['_t']
                    data_type = find_type(t)
                    data = data_type(data = data)
                except KeyError:
                    pass
            self._data = data
            return data
        return None
            
class ResponseContext():
    status = 0
    message = ''
    data = None
    allow_actions = []
    cache_control = None
    connection = None
    
    language = None
    alternate_location = None
    mime_type = ''
    send_date = None
    data_expires = None
    last_modified = None
    new_location = None
    application_string = None
    cookies = {}
    
    def __init__(self,endpoint):
        self.endpoint = endpoint
        self.status = endpoint.STATUS_SUCCESS
        self.app = endpoint.app
        self._data = None
        self._data_range = None
        self._data_stream = None
        self._compression = None
        self._data_encoding = None
        self.application_string = self.app.application_string
       
    @property
    def data_stream(self):
        if self._data_stream:
            return self._data_stream
            
        if not self._data:
            return None
            
        if isinstance(self.data,bytes):
            self._data_stream = self.data
        else:
            formatter = get_formatter(self.context,True)
            if formatter:
                self._data_stream = formatter.encode(self.data)
            else:
                self.not_acceptable()
                
        self._data_stream, self._compression = compress_data(self.context,self._data_stream)
        if self._data_range:
            self._data_stream = self._data_stream[self._data_range]
        
        return self._data_stream
        
    @property
    def data(self):
        return self._data
        
    @data.setter
    def data(self,value):
        self._data = value
        self._data_stream = None
        
    @property
    def compression(self):
        return self._compression
        
    @property
    def data_encoding(self):
        return self._data_encoding
        
    @property
    def data_length(self):
        ds = self.data_stream
        if not ds:
            return None
        return len(ds)
        
    @property
    def data_hash(self):
        ds = self.data_stream
        if not ds:
            return None
        hasher = hashlib.md5()
        hasher.update(ds)
        return str(base64.b64encode(hasher.digest()),'latin-1')
        
    # @property
    # def response_id(self):
        # ds = self.data_stream
        # if not ds:
            # return None
        # hasher = hmac.new(bytes(self.app.hash_key,'utf-8'))
        # hasher.update(ds)
        # return str(base64.b64encode(hasher.digest()),'latin-1')
        
    @property
    def data_range(self):
        if not self._data_range:
            return None
        return '%d-%d'%(self._data_range.start, self._data_range.stop)
        
    @data_range.setter
    def data_range(self,value):
        self._data_range = value
        self._data_stream = None
        if value:
            self._data_encoding = 'chuncked'
        else:
            self._data_encoding = None
            
    @property
    def set_cookie(self):
        return ';'.join(map(lambda i: '%s=%s'%i,self.cookies.items()))

    def not_found(self, message=''):
        self.send_error(self.endpoint.STATUS_NOT_FOUND,message)
        
    def redirect(self,location):
        self.redirect_location = location
        self.send_error(self.endpoint.STATUS.REDIRECT)
        
    def action_not_allowed(self):
        self.send_error(self.endpoint.STATUS_ACTION_NOT_ALLOWED)
        
    def unauthorized(self):
        self.send_error(self.endpoint.STATUS_UNAUTHORIZED)
        
    def permission_error(self):
        self.send_error(self.endpoint.STATUS_PERMISSION_ERROR)
        
    def bad_request(self):
        self.send_error(self.endpoint.STATUS_BAD_REQUEST)
        
    def internal_error(self,error=None):
        if isinstance(error,Exception):
            error = str(error)
        self.send_error(self.endpoint.STATUS_INTERNAL_ERROR,error)
        
    def not_modified(self):
        self.send_error(self.endpoint.STATUS_NOT_MODIFIED)
        
    def not_acceptable(self):
        self.send_error(self.endpoint.STATUS_NOT_ACCEPTABLE)
    
    def send_error(self,status,message=None):
        self.status = status
        if message:
            self.message = message
            self.data = bytes(message,'utf-8')
            self.content_type = 'text/text; charset=utf-8'
        if status > 0:
            raise StopExecutionException()

    def finalize(self):
        formatter = self.app.find_formatter(self.context.request)
        

class ExecutionContext():
    endpoint = None
    controller = None
    action = ''
    app = None
    user = None
    variables = {}
    
    def __init__(self,request,response):
        self.request = request
        self.response = response
        
        request.context = self
        response.context = self
        
        self.app = request.app
        
