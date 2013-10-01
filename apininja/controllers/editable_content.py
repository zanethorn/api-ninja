from apininja.controllers import Controller
from .static_content import StaticContentController
from apininja.log import log
from apininja.helpers import *
from apininja.actions import *
import os, time
import mimetypes
import email.utils

class EditableContentController(StaticContentController):

    def get_allowed_actions(self,resource):
        if os.path.isdir(resource):
            return [LIST,GET,CREATE]
        elif os.path.exists(resource):
            return [GET,UPDATE,DELETE]
        else:
            return [UPDATE]
            
    def create(self, resource):
        if not os.path.exists(resource):
            self.response.not_found()
        elif not os.path.isdir(resource):
            self.response.action_not_allowed()
            
        try:
            name = self.request.variables['name']
        except KeyError:
            try:
                ext = self.request.variables['ext']
            except KeyError:
                ext = '.txt'
            name = self.create_file_name(ext)
            
        data = self.request.data
        path =os.path.join(resource,name)
        with open(path,'wb') as file:
            file.write(data)
        return None
        
    def update(self, resource):
        if not os.path.exists(resource):
            self.response.not_found()
        
        data = self.request.data
        with open(resource,'wb') as file:
            file.write(data)
        return None
        
    def delete(self, resource):
        if not os.path.exists(resource):
            self.response.not_found()
            
        os.remove(resource)
        return None
        
    def create_file_name(self,extension='.txt'):
        name = random_string(8) + extension
        return name