from .controller import Controller, verbs
from ..log import log
import os, time
import mimetypes
import email.utils

if not mimetypes.inited:
    mimetypes.init()


class Static_ContentController(Controller):
    content_folder = 'content'
    cache = 'max-age=3600'
    allow_anonymous = True
    allow_directory_listing = False
    
    def _handle_value(self,name,value):
        setattr(self,name,value)
    
    def get(self,*path):
        path = '/'.join(path)
        app_root = self.context.app.app_root
        path = os.path.join(os.path.join(app_root,self.content_folder),path)
        
        if os.path.isdir(path):
            if not self.allow_directory_listing:
                path = os.path.join(path,'index.html')
            else:
                return self.list(path)
        
        log.debug('trying to find path %s'%path)
        if not os.path.exists(path):
            self.response.not_found()
            
        mime_type = 'application/octet-stream'
        ix = path.rfind('.')
        ext = path[ix:]
        try:
            mime_type = mimetypes.types_map[ext]
        except KeyError:
            pass
        log.debug('suggested MIME type %s'%mime_type)
        self.response.content_type=  mime_type
        self.response.variables['Cache-Control']= self.cache
        
        m_time = os.path.getmtime(path)
        self.response.variables[''] = email.utils.formatdate(m_time)
        if 'If-Modified-Since' in self.request.variables:
            parsed=email.utils.parsedate(self.request.variables['If-Modified-Since'])
            last_modified = time.mktime(parsed)
            if last_modified > m_time:
                self.response.data = None
                self.response.not_modified()
        
        self.response.variables['Last-Modified'] = email.utils.formatdate(m_time)
            
        with open(path,'rb') as file:
            return file.read()
            
    def list(self,*path):
        if self.request.protocol == 'ftp':
            if self.request.command =='PWD':
                self.response.send_error(257,path)
            elif self.request.command == 'LIST':
                self.response.connection.send(b'150 Here comes the directory listing.\r\n')
                list = '\r\n'.join(map(lambda p: os.path.join(path,p),os.listdir(path)))
                self.response.connection.send(bytes(list,'latin-1'))
                self.response.send_error(266,'Directory send OK.')