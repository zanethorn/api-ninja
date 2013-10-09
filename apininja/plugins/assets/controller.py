from apininja.controllers.editable_content import EditableContentController
from apininja.data import *
from apininja.log import log
from apininja.actions import *
from apininja.mime_types import *
import os, time, datetime


class AssetController(EditableContentController):
    database = ''
    content_folder = 'assets'
    container_name='assets'
    db = None
    container = None
    
    def execute(self):
        self.db = None
        try:
            self.db = self.get_database()
            self.container = self.get_container()
            if not self.db:
                self.response.internal_error('Database \'%s\' is not configured!'%self.database)
            result = super().execute()
            #self.response.cache_control = 'no-cache'

            return result
        finally:
            if self.db:
                del self.db
    
    def get_database(self):
        return self.app.get_database(self.database,self.context)

    def get_container(self):
        return self.db.get(self.container_name)
        
    def get_allowed_actions(self,resource):
        return super().get_allowed_actions(resource[0])
        
    def get_last_modified(self,resource):
        if isinstance(resource,DataObject):
            return resource.last_modified
        return super().get_last_modified(resource[0])
    
    def locate_resource(self,path):
        app_root = self.context.app.app_root
        base_path = os.path.join(app_root,self.content_folder)
        content_path = base_path
        
        for p in path:
            content_path = os.path.join(content_path,p)
            
        log.debug('asset controller found content path %s',content_path)
        if self.context.action == LIST:
            if resource !=base_path:
                self.response.action_not_allowed()
                
        if os.path.isdir(content_path):
            return (content_path, None)
            
        asset = self.container.get(content_path)
        if not asset:
            self.response.not_found()
            
        return (content_path,None)
            
    def create(self, resource):
        app_root = self.context.app.app_root
        content_path = os.path.join(app_root,self.content_folder)
        
        raw_file = self.request.data
        orig_filename = self.request.variables['filename']
        filename = orig_filename.lower()
        
        fn,ext = os.path.splitext(filename)
        filename = 'source'+ext
        
        uid = self.context.user.id
        path = os.path.join(content_path,str(uid))
        
        data = {
            'original_filename':fn,
            'original_extension':ext,
            'file_extension':ext,
            'mime_type':mime_types[ext],
            'filename':filename,
            'file_size':len(raw_file),
            'rotation':0,
            'date':datetime.datetime.utcnow(),
            'title': os.path.splitext(orig_filename)[0],
            '_t':self.container.item_type,
            'owner_id':self.context.user.id
            }
        
        asset = self.container.create(data)
        asset_id = asset.id
        
        path = os.path.join(path,str(asset_id))
        os.makedirs(path)
        path = os.path.join(path,filename)
        try:
            
            with open(path,'wb') as file:
                file.write(raw_file)
                file.flush()
                file.close()
            
            asset.path = path
            asset._data['uri'] = '/%s/%s/%s/%s'%(self.content_folder,uid,asset.id,filename)
            asset = self.container.update(asset, server_only=True)
            log.debug('Returning asset with id %s uri %s',asset.id,asset.uri)
            return asset
        except:
            self.container.delete(asset)
            raise

    def update(self, resource):
        path = resource[0]
        asset = resource[1]
        
        with open(path,'wb') as file:
            file.write(self.request.data)
            
        self.container.save(asset)
        return asset
        
    def delete(self, resource):
        path = resource[0]
        asset = resource[1]
        
        try:
            os.remove(path)
        except OSError:
            pass
            
        self.container.delete(asset)
        return None
        
    def get(self, resource):
        path = resource[0]
        asset = resource[1]
        
        if not os.path.exists(path):
            self.response.not_found()
            
        ix = path.rfind('.')
        ext = path[ix:]
        try:
            self.response.mime_type = mime_types[ext]
        except KeyError:
            pass
            
        self.response.cache_control = self.cache
        
        with open(path,'rb') as file:
            return file.read()
        
    def list(self,resource):
        super().list(resource[0])