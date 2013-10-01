from apininja.data.formatters import Formatter
from apininja.data import *
import json
from datetime import datetime

class FtpFormatter(Formatter):

    def encode(self, data):
        if isinstance(data,list):
            return self.encode_list(data)
        return bytes(json.dumps(data,default=handle_default),'utf-8')

    def encode_list(self,data):
        return bytes('\r\n'.join(data),'utf-8')
        
    def decode(self,data,**kwargs):
        return json.loads(str(data,'utf-8'))