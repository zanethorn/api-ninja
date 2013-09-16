import traceback
from .log import log

class StopExecutionException(Exception):
    pass

class RequestContext():
    protocol = ''
    endpoint = None
    client = None
    raw_request = None
    variables = {}
    path = ''
    version=''
    command = ''
    
    def __init__(self,endpoint):
        self.endpoint = endpoint
        self.protocol = endpoint.protocol
        self.app = endpoint.app
        
class ResponseContext():
    variables = {}
    status = 0
    message = ''
    data = None
    _content_type= 'text/text'
    is_binary = False
    complete = False
    
    def __init__(self,endpoint):
        self.endpoint = endpoint
        self.status = endpoint.STATUS_SUCCESS
        self.app = endpoint.app
    
    def get_content_type(self):
        return self._content_type
        
    def set_content_type(self,value):
        self._content_type = value
        self.variables['Content-type'] = value
        #traceback.print_stack()
        #log.debug('content type changed!')
        
    content_type = property(get_content_type,set_content_type)
    
    def not_found(self, message=''):
        self.send_error(self.endpoint.STATUS_NOT_FOUND,message)
        
    def redirect(self,location):
        self.header['Location'] = location
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
        if error:
            error = str(error)
        self.send_error(self.endpoint.STATUS_INTERNAL_ERROR,error)
        
    def not_modified(self):
        self.send_error(self.endpoint.STATUS_NOT_MODIFIED)
    
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
    
    def __init__(self,request,response):
        self.request = request
        self.response = response
        
        request.context = self
        response.context = self
        
        self.app = request.app