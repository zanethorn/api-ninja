from apininja.data import *
from apininja.helpers import *
from apininja.log import log
import os

log.debug('Loading assets')

@known_type('asset')
class Asset(DataObject):
    uri = attribute(type='str')
    file_extension = attribute(type='str')
    mime_type = attribute(type='str')
    file_size = attribute(type='int')
    original_extension = attribute(type='str', server_only=True)
    original_filename = attribute(type='str', server_only=True)
    original_folder = attribute(type='str', server_only=True)
    rotation = attribute(type='int',default=0)
    albums = attribute(type='list', item_type='oid', default=[])
    path = attribute(type='str', server_only=True)
    title = attribute(type='str')
    date = attribute(type='datetime')

@known_type('assets')    
class Assets(DataContainer):
    item_type= 'asset'
    
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
  