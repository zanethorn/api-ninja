from apininja.data.formatters import Formatter
from apininja.data import *
from apininja.helpers import *

class TextFormatter(Formatter):
    mime_types=['text/text','*/*']
    format='text'
    
    def encode(self,data):
        return bytes(str(data),'utf-8')