from apininja.data import *
from apininja.helpers import *
from apininja.log import log
import os

log.debug('Loading assets')

@known_type('asset')
class Asset(DataObject):
    uri = attribute()
    file_extension = attribute()
    mime_type = attribute(type='str')
    file_size = attribute(type='int')
    original_extension = attribute(server_only=True)
    original_filename = attribute(server_only=True)
    original_folder = attribute(server_only=True)
    rotation = attribute(type='int',default=0)
    flags = attribute(default=[])
    albums = attribute(default=[])
    path = attribute(server_only=True)

@known_type('assets')    
class Assets(DataContainer):
    item_type= 'asset'
    
    # def create(self,rfile,filename):
        # fn,ext = os.path.splitext(filename)
        # filename = 'source'+ext
        # data = {
            # 'original_filename':fn,
            # 'original_extension':ext,
            # 'filename':filename,
            # '_t':self.item_type
            # }
        # data =super().create(data)
        # id = data['_id']
        # folder = self.user.id + '/' + str(id)
        # file_location = folder + '/'+filename
        # path = './__files__/'+file_location
        # try:
            # os.makedirs('./__files__/'+folder)
        # except OSError:
            # pass
        # data['path'] = path
        # data['uri'] =  '/files/'+file_location
        
        # try:
            # with open(path,'wb') as file:
                # file.write(rfile)
            # self._inner.save(data)
        # except:
            # os.remove(path)
            # raise
        
        # item = self.create_item(data)
        # return item

    def _delete_item(self,item):
        
        os.remove(item.path)
        super()._delete_item(item)
        
    def get_id_query(self,id):
        if isinstance(id,dict):
            return id
        pid = self.data_adapter.parse_key(id)
        if type(pid) == self.data_adapter.key_type:
            return {'_id':pid}
        if isinstance(id,str):
            return {'path':id}
        return super().get_id_query(id)
  