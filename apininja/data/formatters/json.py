from apininja.data.formatters import Formatter
from apininja.data import *
import json
from datetime import datetime

try:
    #from bson.objectid import ObjectId
    from bson.dbref import DBRef
except ImportError:
    #class ObjectId(): pass
    class DBRef(): pass
    
def handle_default(item):
    if isinstance(item,datetime):
        #item.microsecond = 0
        return item.strftime("%Y-%m-%dT%H:%M:%SZ")
    elif isinstance(item,DBRef):
        return {'collection':item.collection,'_id':item.id,'_t':'ref'}
    elif isinstance(item,DataObject):
        # if not item.id:
            # log.error('%s does not have an id',item)
            # raise RuntimeError()
        return item.to_simple()
    else:
        try:
            s= str(item)
            log.debug('converted item %s to %s',item, s)
            return s
        except:
            raise TypeError('cannot format %s'%item.__class__.__name__)

class JsonFormatter(Formatter):
    mime_types=['application/json']
    format = 'json'

    def encode(self, data):
        return bytes(json.dumps(data,default=handle_default),'utf-8')

    def decode(self,data,**kwargs):
        return json.loads(str(data,'utf-8'))