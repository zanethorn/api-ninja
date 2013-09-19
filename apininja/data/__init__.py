from apininja.helpers import bootstrap_namespace
from .dataobject import *
from .container import *
import importlib, os

from apininja.log import log
log.info('Initializing apininja.data namespace')

#__all__ = ['adapters','formatters','database']
