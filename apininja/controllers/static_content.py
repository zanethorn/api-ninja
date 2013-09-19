﻿#from .controller import Controller, verbs
from apininja.controllers import Controller
from apininja.log import log
from apininja.actions import *
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
    
    def locate_resource(self,path):
        app_root = self.context.app.app_root
        content_path = os.path.join(app_root,self.content_folder)
        for p in path:
            content_path = os.path.join(content_path,p)
        if os.path.isdir(content_path):
            if not self.allow_directory_listing:
                path = os.path.join(content_path,'index.html')
            else:
                return self.list(content_path)
        
        if not os.path.exists(content_path):
            self.response.not_found()
        
        ix = content_path.rfind('.')
        ext = content_path[ix:]
        try:
            self.response.mime_type = mimetypes.types_map[ext]
        except KeyError:
            pass
            
        self.response.cache_control = self.cache
        
        m_time = os.path.getmtime(content_path)
        self.response.last_modified =m_time# email.utils.formatdate(m_time)
        # if 'If-Modified-Since' in self.request.variables:
            # parsed=email.utils.parsedate(self.request.variables['If-Modified-Since'])
            # last_modified = time.mktime(parsed)
            # if last_modified > m_time:
                # self.response.data = None
                # self.response.not_modified()
        
        return content_path
        
    def get_allowed_actions(self,resource):
        if os.path.isdir(resource):
            return [LIST,GET]
        else:
            return [GET]
        
    def get(self,resource):
        with open(resource,'rb') as file:
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