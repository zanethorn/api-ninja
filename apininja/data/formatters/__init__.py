from apininja.log import log
from apininja.helpers import *
import gzip, zlib, bz2, lzma
log.info('Initializing apininja.data.formatters namespace')

class FormatterMetaclass(SelfRegisteringType):
    extension = 'Formatter'

class Formatter(metaclass = FormatterMetaclass):
    mime_types=[]
    format = ''
    
    def __init__(self, context):
        self.context = context
        self.app = context.app

    def encode(self, data):
        raise NotImplementedError()

    def decode(self,data):
        raise NotImplementedError()

def map_format(format):
    for t in FormatterMetaclass.known_types.values():
        if t.format == format:
            return t.mime_types
    return None
    
def get_formatter(context, response=True):
    types = FormatterMetaclass.known_types.values()
    formats = []
    if response:
        if context.response.mime_type:
            formats = [ context.response.mime_type ]
        else:
            try:
                f = context.variables['format']
                if f:
                    formats = map_format(f)
            except KeyError:
                pass
            
            if not formats:
                formats = context.request.allowed_types
    else:
        formats = [ context.request.mime_type ]        
    
    log.debug('finding formatter for %s',formats)
    for f in types:
        for t in f.mime_types:
            if t in formats:
                if response:
                    context.response.mime_type = t
                return f(context)
    return None
    
def compress_data(context,data):
    if context.request.allowed_compression:
        for ctype in context.request.allowed_compression:
            try:
                compressor = compressors[ctype]
                encoded = compressor(data)
                log.debug('Compressing data with %s',ctype)
                return encoded, ctype
            except KeyError:
                pass
                
    return data, None
    
def decompress_data(context,data):
    if context.request.compression:
        try:
            decompressor = decompressors[context.request.compression]
            decoded = decompressor(data)
            return decoded
        except KeyError:
            raise ValueError('Unable to locate decompressor for %s'%context.request.compression)
                
    return data
    
compressors = {
    'lzma':lzma.compress,
    'gzip':gzip.compress,
    'deflate':zlib.compress,
    'bzip2':bz2.compress
    }
    
decompressors = {
    'lzma':lzma.decompress,
    'gzip':gzip.decompress,
    'deflate':zlib.decompress,
    'bzip2':bz2.decompress
    }
        
# import remaining files in package to initialize them
my_path = os.path.dirname(__file__)
all = []
for d in os.listdir(my_path):
    if d[-3:] == '.py' and d != '__init__.py':
        importlib.import_module('.'+d[:-3],__package__)