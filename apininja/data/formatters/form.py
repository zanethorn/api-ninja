from apininja.data.formatters import Formatter
import urllib

class FormFormatter(Formatter):
    mime_type=['application/x-www-form-urlencoded','application/www-form-urlencoded']
    format = 'form'
    
    def decode(self,data,**kwargs):
        raw= urllib.parse.parse_qs(data)
        for prop,val in raw.items():
            if isinstance(val,list) and len(val) ==1:
                raw[prop]=val[0]
        return raw