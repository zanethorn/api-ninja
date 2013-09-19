from apininja.log import log
from apininja.helpers import *
log.info('Initializing apininja.data.formatters namespace')

class FormatterMetaclass(SelfRegisteringType):
    extension = 'Formatter'

class Formatter(metaclass = FormatterMetaclass):
    mime_types=[]
    format = ''
    
    def __init__(self, context):
        self.context = context
        self.app = context.app

    def encode(self, data, user, **kwargs):
        if isinstance(data,list):
            return self.encode_list(data,user,**kwargs)
        return self.encode_item(self,data,user,**kwargs)

    def encode_list(self,data,user,**kwargs):
        raise NotImplemented()

    def encode_item(self,data,user,**kwargs):
        raise NotImplemented()

    def decode(self,data,**kwargs):
        raise NotImplemented()

# import remaining files in package to initialize them
my_path = os.path.dirname(__file__)
all = []
for d in os.listdir(my_path):
    if d[-3:] == '.py' and d != '__init__.py':
        importlib.import_module('.'+d[:-3],__package__)