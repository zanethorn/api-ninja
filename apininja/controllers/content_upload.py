from apininja.controllers import Controller
from .editable_content import EditableContentController
from apininja.log import log
from apininja.actions import *
import os, time
import mimetypes
import email.utils

class ContentUploadController(EditableContentController):
    def get_allowed_actions(self,resource):
        return [CREATE]
            
    def create(self, resource):
        raise NotImplementedError()
        
    def update(self, resource):
        self.response.action_not_allowed()
        
    def delete(self, resource):
        self.response.action_not_allowed()
        
    def list(self, resource):
        self.response.action_not_allowed()
        
    def get(self, resource):
        self.response.action_not_allowed()