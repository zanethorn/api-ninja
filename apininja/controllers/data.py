#from .controller import Controller, verbs
from apininja.controllers import Controller
from apininja.log import log
from apininja.data import *
from apininja.data.formatters import *
from apininja.actions import *
import os, time
import mimetypes
import email.utils

if not mimetypes.inited:
    mimetypes.init()


class DataController(Controller):
    database = ''
    db = None
    
    def get_database(self):
        return self.app.get_database(self.database,self.context)
        
    def get_allowed_actions(self,resource):
        if isinstance(resource,DataContainer):
            return [LIST,CREATE]
        else:
            return [GET,UPDATE,DELETE]
        
    def locate_resource(self,path):
        working = self.db
        for p in path:
            working = working.get(p)
            if not working:
                self.response.not_found()
        return working
        
    def get(self,resource):
        if isinstance(resource,DataContainer):
            return self.list(resource)
        return resource
    
    def list(self, resource):
        result = list(resource.list(self.request.query,self.request.options))
        return result
        
    def create(self, resource):
        pass
    
    def update(self, resource):
        pass
        
    def delete(self, resource):
        pass
    
    def execute(self):
        self.db = None
        try:
            self.db = self.get_database()
            if not self.db:
                self.response.internal_error('Database \'%s\' is not configured!'%self.database)
            result = super().execute()
            
            return result
        finally:
            if self.db:
                del self.db
           
    def format_content(self,content):
        fcls = self.get_formatter()
        if not fcls:
            self.response.not_acceptable()
        def extract_data(d):
            if isinstance(d,DataObject):
                return d._data
            elif isinstance(d,list):
                return [ extract_data(i) for i in d]
            elif isinstance(d,dict):
                return { k:extract_data(v) for k,v in d.items() }
            else:
                return d
        content = extract_data(content)
        formatter = fcls(self.context)
        return formatter.encode(content)

    def get_formatter(self):
        types = FormatterMetaclass.known_types.values()
        log.debug('finding formatter in %s',self.request.allowed_types)
        if 'format' in self.context.variables:
            format = self.context.variables['format']
            for f in types:
                if f.format == format:
                    self.response.mime_type = format
                    return f
                    
        for f in types:
            for t in f.mime_types:
                if t in self.request.allowed_types:
                    self.response.mime_type = t
                    return f