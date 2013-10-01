from apininja.log import log
from apininja.helpers import bootstrap_namespace
from .users import *
from .root import *
from .unauthorized import *
log.info('Initializing apininja.security namespace')

# import remaining files in package to initialize them
my_path = os.path.dirname(__file__)
all = []
for d in os.listdir(my_path):
    if d[-3:] == '.py' and d != '__init__.py':
        importlib.import_module('.'+d[:-3],__package__)
        
root = root
unauthorized = unauthorized