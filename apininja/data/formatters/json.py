from apininja.data.formatters import Formatter
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
        return item.isoformat()
    elif isinstance(item,DBRef):
        return {'collection':item.collection,'id':item.id,'_t':'ref'}
    else:
        try:
            return str(item)
        except:
            raise TypeError('cannot format %s'%item.__class__.__name__)

class JsonFormatter(Formatter):
    mime_types=['application/json']
    format = 'json'

    def encode(self, data):
        return bytes(json.dumps(data,default=handle_default),'utf-8')

    def decode(self,data,**kwargs):
        print('raw data',data)
        return json.loads(data)