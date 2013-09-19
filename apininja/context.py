import traceback
import hashlib, base64
from .log import log

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
    data = None
    query = {}
    options = {}
    
    allowed_types = []
    allowed_charsets = []
    allowed_compression = []
    allowed_language = []
    authorization = None
    cache_control = None
    connection = None
    data_length = 0
    data_hash = None
    mime_type = None
    send_date = None
    expect = None
    username = None
    host = None
    sender = None
    
    def __init__(self,endpoint):
        self.endpoint = endpoint
        self.protocol = endpoint.protocol
        self.app = endpoint.app
        
class ResponseContext():
    status = 0
    message = ''
    data = None
    allow_actions = []
    cache_control = None
    connection = None
    compression = None
    language = None
    alternate_location = None
    mime_type = 'application/octet-stream'
    send_date = None
    data_uid = None
    data_expires = None
    last_modified = None
    new_location = None
    application_string = None
    data_encoding = None
    
    def __init__(self,endpoint):
        self.endpoint = endpoint
        self.status = endpoint.STATUS_SUCCESS
        self.app = endpoint.app
        self._data = None
        self._data_range = None
        self.application_string = self.app.application_string
    
        
    @property
    def data(self):
        if self._data_range:
            return self._data[self._data_range]
        return self._data
        
    @data.setter
    def data(self,value):
        self._data = value
        
    @property
    def data_length(self):
        if not self._data:
            return None
        return len(self.data)
        
    @property
    def data_hash(self):
        if not self._data:
            return None
        hasher = hashlib.md5()
        hasher.update(self.data)
        return base64.b64encode(hasher.digest())
        
    @property
    def data_range(self):
        if not self._data_range:
            return None
        return '%d-%d'%(self._data_range.start, self._data_range.stop)
        
    @data_range.setter
    def set_data_range(self,value):
        self._data_range = value

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