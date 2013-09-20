from apininja.controllers import Controller
from .static_content import StaticContentController
from apininja.log import log
from apininja.actions import *
import os, time
import mimetypes
import email.utils

class EditableContentController(StaticContentController):
    def get_allowed_actions(self,resource):
        if os.path.isdir(resource):
            return [LIST,GET,POST]
        else:
            return [GET,PUT,DELETE]
            
    def create(self, resource):
        raise NotImplementedError()
        
    def update(self, resource):
        raise NotImplementedError()
        
    def delete(self, resource):
        raise NotImplementedError()