from apininja.controllers import Controller
from apininja.log import log
from apininja.actions import *
from apininja.mime_types import *
import os, time, datetime
import email.utils


class StaticContentController(Controller):
    content_folder = 'content'
    cache = 'max-age=3600'
    allow_anonymous = True
    allow_directory_listing = False
    
    def locate_resource(self,path):
        app_root = self.context.app.app_root
        content_path = os.path.join(app_root,self.content_folder)
        for p in path:
            content_path = os.path.join(content_path,p)
        if os.path.isdir(content_path):
            if self.allow_directory_listing:
                path = os.path.join(content_path,'index.html')
        
        if not os.path.exists(content_path):
            self.response.not_found()
        
        ix = content_path.rfind('.')
        ext = content_path[ix:]
        try:
            self.response.mime_type = mime_types[ext]
        except KeyError:
            pass
            
        self.response.cache_control = self.cache

        return content_path
        
    def get_last_modified(self,resource):
        if not os.path.exists(resource):
            return None
        return datetime.datetime.utcfromtimestamp(os.path.getmtime(resource))
        
    def get_allowed_actions(self,resource):
        print(resource)
        if os.path.isdir(resource):
            return [LIST,GET]
        else:
            return [GET]
        
    def get(self,resource):
        if not os.path.exists(resource):
            self.response.not_found()
            
        with open(resource,'rb') as file:
            return file.read()
            
    def list(self,resource):
        if not os.path.exists(resource):
            self.response.not_found()
        return os.listdir(resource)