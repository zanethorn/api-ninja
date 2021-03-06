﻿import traceback
import hashlib, base64, hmac
from apininja.log import log
from apininja.data.formatters import *
from apininja.data import *
from apininja.security import unauthorized

class StopExecutionException(Exception):
    pass

class RequestContext():

    client = None
    raw_request = None
    path = ''
    version=''
    command = ''
    content_type= None
    
    data_length = 0
    compression = None
    
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
        self.query = {}
        self.options = {}
        self.variables = {}
        self.allowed_types = []
        self.allowed_charsets = []
        self.allowed_compression = []
        self.allowed_language = []
    
    @property
    def data(self):
        if self._data:
            return self._data
        if not self.data_length:
            return None
        
        if not self._data and self.data_length:
            raw = bytes()#self._dstream.read(self.data_length)
            bytes_read = 0;
            while bytes_read <  self.data_length:
                offset = self.data_length - bytes_read
                d = self._dstream.read(offset)
                if d:
                    raw+=d
                    bytes_read +=len(d)
            
            if self.compression:
                #log.debug('decompressing data stream with %s',self.compression)
                raw = decompress_data(self.context,raw)
            #log.debug('Request body len: %d (says %s)',len(raw),self.data_length)
            formatter = self.app.get_formatter(self.context,False)
            #log.debug('Found formatter %s',formatter)
            if formatter:
                data = formatter.decode(raw)
            else:
                data = raw
                
            if isinstance(data,dict):
                try:
                    t = data['_t']
                    data_type = find_type(t)
                    source = { '_t':t }
                    try:
                        source['_id'] = data['_id']
                    except KeyError:
                       pass
                    obj = data_type(data = source, context=self.context)
                    for attr in data_type.__attributes__:
                        try:
                            val  = data[attr.name]
                            setattr(obj,attr.name,val)
                        except:
                           pass
                    data = obj
                except KeyError:
                   pass
            self._data = data
            return data
        return None
            
class ResponseContext():

    def __init__(self,endpoint):
        self.endpoint = endpoint
        self.status = endpoint.STATUS_SUCCESS
        self.app = endpoint.app
        self.message = ''
        self.allow_actions = []
        self._data = None
        self._data_range = None
        self._data_stream = None
        self._compression = None
        self._data_encoding = None
        self.cache_control = None
        self.connection = None
        self.language = None
        self.alternate_location = None
        self.mime_type = ''
        self.send_date = None
        self.data_expires = None
        self.last_modified = None
        self.new_location = None
        self.application_string = None
        self.variables = {}
        self.application_string = self.app.application_string
       
    @property
    def data_stream(self):
        if self._data_stream:
            return self._data_stream
            
        if not self._data:
            return None
        
        log.debug('Outgoing context data type %s',type(self.data))
        if isinstance(self.data,bytes):
            self._data_stream = self.data
        else:
            formatter = self.app.get_formatter(self.context,True)
            if formatter:
                log.debug('Encoding data with %s',type(formatter).__name__)
                self._data_stream = formatter.encode(self.data)
            else:
                self.not_acceptable()
        
        data, compression = compress_data(self.context,self._data_stream)
        self._data_stream = data
        self._compression = compression
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
        self._compression = None
        
    @property
    def compression(self):
        ds = self.data_stream
        if not ds:
            return None
        return self._compression
        
    @property
    def data_encoding(self):
        ds = self.data_stream
        if not ds:
            return None
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
            
    def conflict(self,message=''):
        self.send_error(self.endpoint.STATUS_CONFLICT,message)

    def not_found(self, message=''):
        self.send_error(self.endpoint.STATUS_NOT_FOUND,message)
        
    def redirect(self,location):
        self.redirect_location = location
        self.send_error(self.endpoint.STATUS.REDIRECT)
        
    def action_not_allowed(self):
        self.send_error(self.endpoint.STATUS_ACTION_NOT_ALLOWED)
        
    def unauthorized(self,message=None):
        self.send_error(self.endpoint.STATUS_UNAUTHORIZED,message=message)
        
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
    
    # variables = {}
    
    def __init__(self,request,response):
        self.endpoint = None
        self.controller = None
        self.action = ''
        self.user = unauthorized
        
        self.request = request
        self.response = response
        
        request.context = self
        response.context = self
        
        self.app = request.app
        
