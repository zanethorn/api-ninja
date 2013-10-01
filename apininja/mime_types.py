import mimetypes
from copy import copy

mime_types = copy(mimetypes.types_map)
mime_types['.png'] = 'image/png' 
mime_types['.jpg'] = 'image/jpeg'
mime_types['.jpeg'] = 'image/png'  

mime_types['.htm'] = 'text/html'
mime_types['.html'] = 'text/html'  
mime_types['.json'] = 'application/json'
mime_types['.txt'] = 'text/text'    
