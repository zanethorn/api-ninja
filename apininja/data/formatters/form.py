from apininja.data.formatters import Formatter
from apininja.data import *
from apininja.log import log
import urllib.parse
from copy import copy

parsable_types = copy(simple_types)
parsable_types.remove(str)
parsable_types.remove(bool)

class FormFormatter(Formatter):
    mime_types=['application/x-www-form-urlencoded','application/www-form-urlencoded']
    format = 'form'
    
    def decode(self,data):
        raw = str(data,'utf-8')
        fields = raw.split('&')
        
        fields = { k: v for k,v in map(lambda i: i.split('=',maxsplit=1),fields) }
        log.debug('found fields %s',fields.keys())
        root = {}

        for k,v in fields.items():
            self.decode_field(k,v,root)
        return root

    def decode_field(self,path,value,root):
        # parse data to a meaningful type
        value = self.decode_value(value,path)
        for t in parsable_types:
            try:
                value = t(value)
                break
            except:
                pass
        
        parts = path.split('_')
        working = root
        lparts = len(parts)-1
        for i,p in enumerate(parts):
            ix = None
            # get index for indexed variables
            if '[' in p:
                p, ix = p.split('[',maxsplit=1)
                ix = int(ix.strip(']'))

            if i == lparts:
                # set value
                if ix is None:
                    working[p] = value
                else:
                    if not p in working:
                        working[p] = [ None for i in range(ix+1)]
                    lst = working[p]
                    len_list = len(lst)
                    if len_list <= ix:
                        d = ix - len_list
                        lst += [ None for i in range(d,d+1)]
                        working[p] = lst
                    lst[ix] =value
            else:
                if not p in working:
                    if ix is not None:
                        working[p] = []
                    else:
                        working[p] = {}
                    
                working = working[p]
                if ix is not None:
                    working = working[ix]
            
    def decode_value(self,value,path):
        return urllib.parse.unquote_plus(value)
        
    def encode(self,data):
        return bytes(self.encode_val(data),'utf-8')
        
    def encode_val(self,data,path=''):
        if isinstance(data,dict):
            return self.encode_dict(data,path)
        elif isinstance(data,DataObject):
            return self.encode_dict(data.to_dict(),path)
        elif isinstance(data,list):
            return self.encode_list(data,path)
        else:
            return '%s=%s'%(path,urllib.parse.quote_plus(str(data)))
        
    def encode_dict(self,item,path=''):
        segments =[]
        for prop,val in item.items():
            if path:
                pname = '%s_%s'%(path,prop)
            else:
                pname = prop
            segments.append(self.encode_val(val,pname))
            
        return '&'.join(segments)
        
    def encode_list(self,item,path=''):
        segments =[]
        for ix,val in enumerate(item):
            pname = '%s[%d]'%(path,ix)
            segments.append(self.encode_val(val,pname))
            
        return '&'.join(segments)
        
if __name__ == '__main__':
    class DummyContext():
        app = {}
        request = {}
        response ={}
    
    test_data = {
        'first':'Mike',
        'last':'Mulligan',
        'vehical':{
                'type':'Steam Shovel',
                'jobs':[
                    'Dig holes',
                    'Make noise'
                    ]
            }
        }
        
    formatter = FormFormatter(DummyContext(),None)
    out = formatter.encode(test_data)
    print(out)
    coded = formatter.decode(out)
    print(coded)
