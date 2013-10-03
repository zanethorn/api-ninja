import logging, os
from .config import config

initialized = False
log = None

def init():
    global log, initialized
    
    app_name = 'AnyApi'
    level = logging.DEBUG
        
    log = logging.getLogger(app_name)
    log.setLevel(level)

    stream_h = logging.StreamHandler()
    stream_h.setLevel(logging.DEBUG)
    stream_formatter = logging.Formatter(' %(thread)d %(levelname)s: %(message)s')
    stream_h.setFormatter(stream_formatter)
    log.addHandler(stream_h)
    try:
        log_path = config['LOGGING']['path']
    except KeyError:
        log_path = os.getcwd() + '/logs/server.log'
      
    try:
        if os.path.exists(log_path):
            os.remove(log_path)
    except FileNotFoundError:
        pass
    file_h = logging.FileHandler(log_path)
    file_h.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(levelname)s:  %(thread)d/%(threadName)s %(asctime)s - %(message)s')
    file_h.setFormatter(file_formatter)
    log.addHandler(file_h)
    
    initialized = True
    
if not initialized:
    init()