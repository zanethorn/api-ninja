from apininja.log import log
from apininja.helpers import *
log.info('Initializing apininja.data.formatters namespace')

compressors = {}
decompressors = {}

try:
    import gzip
    compressors['gzip'] = gzip.compress
    decompressors['gzip'] = gzip.decompress
except ImportError:
    pass

try:
    import zlib
    compressors['zlib'] = zlib.compress
    decompressors['zlib'] = zlib.decompress
except ImportError:
    pass

try:
    import bz2
    compressors['bz2'] = bz2.compress
    decompressors['bz2'] = bz2.decompress
except ImportError:
    pass
    
try:
    import lzma
    compressors['lzma'] = lzma.compress
    decompressors['lzma'] = lzma.decompress
except ImportError:
    pass

class FormatterMetaclass(SelfRegisteringType):
    extension = 'Formatter'

class Formatter(Configurable,metaclass = FormatterMetaclass):
    mime_types=[]
    format = ''
    
    def __init__(self, context, config):
        super().__init__(config)
        self.context = context
        self.app = context.app
        
    @property
    def request(self):
        return self.context.request
        
    @property
    def response(self):
        return self.context.response

    def encode(self, data):
        raise NotImplementedError()

    def decode(self,data):
        raise NotImplementedError()

def map_format(format):
    for t in FormatterMetaclass.known_types.values():
        if t.format == format:
            return t.mime_types
    return None
    

    
    
    
def compress_data(context,data):
    if context.request.allowed_compression:
        for ctype in context.request.allowed_compression:
            try:
                compressor = compressors[ctype]
                encoded = compressor(data)
                log.debug('Compressed data with %s',ctype)
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
    

        
# import remaining files in package to initialize them
my_path = os.path.dirname(__file__)
all = []
for d in os.listdir(my_path):
    if d[-3:] == '.py' and d != '__init__.py':
        importlib.import_module('.'+d[:-3],__package__)