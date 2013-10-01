from .form import *
from apininja.log import log
import urllib, base64

class MultipartFormFormatter(FormFormatter):
    mime_types=['multipart/form-data']
    format = ''
    
    def decode(self,data):
        parts = super().decode(data)
        raw_file = parts['file']
        pads = len(raw_file) % 4
        if pads > 0:
            #log.warning('invalid padding offset %d',pads)
            raw_file += '='*(pads)
        log.debug('len raw %s',len(raw_file))
        file = base64.b64decode(raw_file)
        del parts['file']
        
        self.request.variables.update(parts)
        return file
        
    # def decode_value(self,value,path):
        # if path=='file':
            # return base64.b64decode(value)
        # return super().decode_value(value,path)
        
    def encode(self,data):
        raw = super().encode(self.response.variables)
        return raw+bytes('file=','utf-8')+data