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
        working = self.db.system_container
        for p in path:
            #log.debug('Looking for data fragment %s',p)
            working = working.get(p)
            #log.debug('Found item of type %s',type(working))
            if not working:
                self.response.not_found()
            assert working.id
        return working
        
    def can_access_resource(self,resource):
        return True
        
    def get_last_modified(self,resource):
        if not resource:
            return None
            
        if isinstance(resource,list):
            return max(resource,key=lambda i: i.last_updated).last_updated
        else:
            return resource.last_updated
        
    def get(self,resource):
        if isinstance(resource,DataContainer):
            return self.list(resource)
        return resource
    
    def list(self, resource):
        log.debug('Running list query %s, %s on %s', self.request.query, self.request.options , resource)
        result = list(resource.list(self.request.query,self.request.options))
        self.response.last_modified = self.get_last_modified(result)
        return result
        
    def create(self, resource):
        data = self.context.request.data
        container = resource
        data = container.create(data)
        return data
    
    def update(self, resource):
        data = self.context.request.data
        resource = resource.parent
        data = resource.update(data)
        #log.debug('controller returned %s',data._data)
        return data
        
    def delete(self, resource):
        data = resource
        container = data.parent
        container.delete(data)
        return None
    
    def execute(self):
        self.db = None
        try:
            self.db = self.get_database()
            if not self.db:
                self.response.internal_error('Database \'%s\' is not configured!'%self.database)
            result = super().execute()
            self.response.cache_control = 'no-cache'

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

    